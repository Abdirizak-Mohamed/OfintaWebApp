# system
import json
import logging
import base64
import requests
from requests.auth import HTTPBasicAuth

# django
from django.conf import settings
from django.utils import timezone

# ofinta
from apps.mpesa_gateway.models import ResponseCode, MPesaTransaction, \
    TransactionType, TransactionStatus
from apps.mpesa_gateway.utils import process_success_webhook

logger = logging.getLogger(__name__)


class MPesaGateway:
    content_type = 'application/json'

    def get_access_token(self):
        access_token_url = '{}?grant_type=client_credentials'.format(
            settings.MPESA_OAUTH2TOKEN_URL
        )
        ck = settings.MPESA_CONSUMER_KEY
        cs = settings.MPESA_CONSUMER_SECRET

        if settings.MPESA_TEST_MODE:
            return {'access_token': 'token'}

        response = requests.get(
            access_token_url, auth=HTTPBasicAuth(ck, cs), verify=False
        )
        return response.json()

    def payment(self, payment, amount, phone_number, description=''):
        """
        :param payment: Payment instance
        :param amount: amount of the payment
        :param phone_number: buyer phone number
        :param description: payment description
        :return: make a payment
        """
        api_url = settings.MPESA_STK_PUSH_URL

        # generate headers
        access_token = self.get_access_token().get('access_token')
        if not access_token:
            print('Failed to get access token')
            return {'success': False}

        headers = {"Authorization": "Bearer {}".format(access_token)}

        # generate password
        now = timezone.now()
        timestamp = now.strftime('%Y%m%d%H%M%S')
        password_decoded = '{}{}{}'.format(
            settings.MPESA_BUSINESS_SHORT_CODE,
            settings.MPESA_PASSKEY,
            timestamp
        )
        password_encoded = base64.b64encode(
            bytes(password_decoded, 'utf-8')
        ).decode('ascii')

        payment_data = {
            "BusinessShortCode": settings.MPESA_BUSINESS_SHORT_CODE,
            "Password": password_encoded,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(amount)),
            "PartyA": phone_number,
            "PartyB": settings.MPESA_BUSINESS_SHORT_CODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_RESULT_URL,
            "AccountReference": settings.MPESA_ACCOUNT_REFERENCE,
            "TransactionDesc": description
        }

        if settings.MPESA_TEST_MODE:
            response_text = json.dumps(settings.MPESA_TEST_RESPONSE_200_JSON)
            response_status_code = settings.MPESA_TEST_RESPONSE_STATUS_CODE
            if response_status_code == 200:
                response_json = settings.MPESA_TEST_RESPONSE_200_JSON
            elif response_status_code == 400:
                response_json = settings.MPESA_TEST_RESPONSE_400_JSON
        else:
            response = requests.post(
                api_url, json=payment_data, headers=headers, verify=False
            )
            response_text = response.text
            response_status_code = response.status_code
            response_json = response.json()

        txn = MPesaTransaction.objects.create(
            status=TransactionStatus.NEW,
            transaction_type=TransactionType.PAYMENT,
            amount=amount,
            party_a=phone_number,
            party_b=settings.MPESA_BUSINESS_SHORT_CODE,
            phone_number=phone_number,
            description=description,
            response_data=response_text
        )
        payment.transaction = txn
        payment.save()

        if response_status_code == 200:
            response_code = response_json['ResponseCode']
            if response_code not in dict(ResponseCode.CHOICES).keys():
                response_code = '999'

            txn.response_code = response_code
            txn.checkout_request_id = response_json['CheckoutRequestID']
            txn.merchant_request_id = response_json['MerchantRequestID']
            txn.response_description = response_json['ResponseDescription']
            txn.customer_message = response_json['CustomerMessage']
            txn.save()

            if response_code == ResponseCode.SUCCESS:
                if settings.MPESA_TEST_MODE:
                    process_success_webhook({})

                return {'transaction': txn, 'success': True}

        elif response_status_code == 400:
            error_message = response_json['errorMessage']
            txn.response_description = response_json['errorMessage']
            txn.save()
            if error_message == 'Bad Request - Invalid PhoneNumer':
                txn.set_wrong_number()
            else:
                txn.set_wrong_data()
        else:
            logger.warning(
                'Failed to make a payment. '
                'Status code: {}. Response: {}.'.format(
                    response_status_code, response_text
                )
            )
            txn.set_fail()

        return {'transaction': txn, 'success': False}

    def refund(self, transaction):
        """
        :param transaction: MPesaTransaction instance
        :return: Send money back to the buyer
        """
        api_url = settings.MPESA_STK_REVERSAL_URL

        # generate headers
        access_token = self.get_access_token().get('access_token')
        if not access_token:
            print('Failed to get access token')
            return

        headers = {"Authorization": "Bearer %s" % access_token}

        description = 'Refund'
        refund_data = {
            "Initiator": transaction.party_b,
            "SecurityCredential": settings.MPESA_SECURITY_CREDENTIAL,
            "CommandID": "TransactionReversal",
            "TransactionID": settings.MPESA_BUSINESS_SHORT_CODE,
            "Amount": str(int(transaction.amount)),
            "ReceiverParty": transaction.party_a,
            "RecieverIdentifierType": "4",
            "ResultURL": settings.MPESA_RESULT_URL,
            "QueueTimeOutURL": settings.MPESA_TIMEOUT_URL,
            "Remarks": description,
            "Occasion": ""
        }
        response = requests.post(
            api_url, json=refund_data, headers=headers, verify=False
        )
        if response.status_code == 200:
            response_json = response.json()
            response_code = response_json['ResponseCode']
            if response_code not in dict(ResponseCode.CHOICES).keys():
                response_code = '999'

            MPesaTransaction.objects.create(
                response_code=response_code,
                transaction_type=TransactionType.REVERSAL,
                amount=transaction.amount,
                party_a=settings.MPESA_BUSINESS_SHORT_CODE,
                party_b=transaction.phone_number,
                phone_number=transaction.phone_number,
                description='Refund of transaction {}'.format(transaction.id),
                response_description=response_json['ResponseDescription'],
            )

            if response_code == ResponseCode.SUCCESS:
                return {'success': True}

        else:
            logger.warning(
                'Failed to make a payment. '
                'Status code: {}. Response: {}.'.format(
                    response.status_code, response.text
                )
            )

        return {'success': False}
