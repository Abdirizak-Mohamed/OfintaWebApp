# system
import json
import logging

# django
from django.conf import settings
from django.utils import timezone

# ofinta
from apps.management.orders.constants import PushStatuses, OrderStatus
from apps.mpesa_gateway.models import MPesaTransaction


logger = logging.getLogger(__name__)


def process_success_webhook(request_json):
    """
    Process mpesa webhook
    """
    from apps.management.orders.models import Payment

    response_json_body = request_json.get('Body', {})
    response_json_callback = response_json_body.get('stkCallback', {})

    if settings.MPESA_TEST_MODE:
        response_json_callback = settings.MPESA_TEST_RESPONSE_JSON_CALLBACK

    merchant_request_id = response_json_callback.get('MerchantRequestID', '')
    checkout_request_id = response_json_callback.get('CheckoutRequestID', '')

    mpesa_transaction = MPesaTransaction.objects.filter(
        merchant_request_id=merchant_request_id,
        checkout_request_id=checkout_request_id
    ).last()

    if not mpesa_transaction:
        logger.warning(
            'Transaction with merchant_request_id={} and '
            'checkout_request_id={} not found'.format(
                merchant_request_id, checkout_request_id
            )
        )
        response_json = {'Error': 'Failed to process webhook'}
        response_status_code = 400
        return response_json, response_status_code

    result_code = response_json_callback.get('ResultCode')
    result_desc = response_json_callback.get('ResultDesc', '')

    mpesa_transaction.result_code = result_code
    mpesa_transaction.result_desc = result_desc
    mpesa_transaction.callback_data = json.dumps(request_json)
    mpesa_transaction.save()

    payment = Payment.objects.get(transaction=mpesa_transaction)
    payment.processed_at = timezone.now()
    payment.save()
    order = payment.order

    if not order.pending_transaction:
        return {'success': False}, 400

    order.pending_transaction = False
    order.save()

    if mpesa_transaction.success:

        mpesa_transaction.set_success(payment)
        order.set_paid()

        if order.payment_ran_by_driver:

            order.set_completed()

            order.send_push_to_assigned_driver(
                message=None,
                push_extra={"status": PushStatuses.ORDER_PAY_SUCCEED}
            )
            return {'success': True}, 200
        else:
            # generate and send verification code
            verification_code = order.generate_verification_code()
            if not settings.MPESA_TEST_MODE:
                order.send_verification_code_by_email()
                order.send_verification_code_by_sms()
            return {'verification_code': verification_code}, 200
    else:
        mpesa_transaction.update_status()
        order.send_push_to_assigned_driver(
            message=None,
            push_extra={
                "status": PushStatuses.ORDER_PAY_FAILED,
                "code": mpesa_transaction.result_code,
                "description": mpesa_transaction.result_desc
            },
        )

    return {}, 400
