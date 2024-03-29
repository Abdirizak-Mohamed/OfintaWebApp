# django
from django.db import models
from django.utils import timezone
from django.conf import settings


class ResponseCode:
    """
    0	Success
    1	Insufficient Funds
    2	Less Than Minimum Transaction Value
    3	More Than Maximum Transaction Value
    4	Would Exceed Daily Transfer Limit
    5	Would Exceed Minimum Balance
    6	Unresolved Primary Party
    7	Unresolved Receiver Party
    8	Would Exceed Maximum Balance
    11	Debit Account Invalid
    12	Credit Account Invalid
    13	Unresolved Debit Account
    14	Unresolved Credit Account
    15	Duplicate Detected
    17	Internal Failure
    20	Unresolved Initiator
    26	Traffic blocking condition in place
    """
    SUCCESS = '0'
    INSUFFICIENT_FUNDS = '1'
    LESS_THAN_MIN_TXN_VALUE = '2'
    MORE_THAN_MAX_TXN_VALUE = '3'
    EXCEED_DAILY_TRANSFER_LIMIT = '4'
    EXCEED_MIN_BALANCE = '5'
    UNRESOLVED_PRIMARY_PARTY = '6'
    UNRESOLVED_RECEIVER_PARTY = '7'
    EXCEED_MAX_BALANCE = '8'
    DEBIT_ACCOUNT_INVALID = '11'
    CREDIT_ACCOUNT_INVALID = '12'
    UNRESOLVED_DEBIT_ACCOUNT = '13'
    UNRESOLVED_CREDIT_ACCOUNT = '14'
    DUPLICATE_DETECTED = '15'
    INTERNAL_FAILURE = '17'
    UNRESOLVED_INITIATOR = '20'
    TRAFFIC_BLOCKING_CONDITION = '26'
    UNKNOWN = '999'

    CHOICES = (
        (SUCCESS, 'Success'),
        (INSUFFICIENT_FUNDS, 'Insufficient Funds'),
        (LESS_THAN_MIN_TXN_VALUE, 'Less Than Minimum Transaction Value'),
        (MORE_THAN_MAX_TXN_VALUE, 'More Than Maximum Transaction Value'),
        (EXCEED_DAILY_TRANSFER_LIMIT, 'Would Exceed Daily Transfer Limit'),
        (EXCEED_MIN_BALANCE, 'Would Exceed Minimum Balance'),
        (UNRESOLVED_PRIMARY_PARTY, 'Unresolved Primary Party'),
        (UNRESOLVED_RECEIVER_PARTY, 'Unresolved Receiver Party'),
        (EXCEED_MAX_BALANCE, 'Would Exceed Maximum Balance'),
        (DEBIT_ACCOUNT_INVALID, 'Debit Account Invalid'),
        (CREDIT_ACCOUNT_INVALID, 'Credit Account Invalid'),
        (UNRESOLVED_DEBIT_ACCOUNT, 'Unresolved Debit Account'),
        (UNRESOLVED_CREDIT_ACCOUNT, 'Unresolved Credit Account'),
        (DUPLICATE_DETECTED, 'Duplicate Detected'),
        (INTERNAL_FAILURE, 'Internal Failure'),
        (UNRESOLVED_INITIATOR, 'Unresolved Initiator'),
        (TRAFFIC_BLOCKING_CONDITION, 'Traffic blocking condition in place'),
        (UNKNOWN, 'Unknown code'),
    )


class TransactionType:
    REVERSAL = 1
    PAYMENT = 2

    CHOICES = (
        (REVERSAL, 'TransactionReversal'),
        (PAYMENT, 'CustomerPayBillOnline')
    )


class TransactionStatus:
    NEW = 0
    SUCCESS = 1
    WRONG_PIN = 2
    CANCEL = 3
    WRONG_NUMBER = 4
    EXPIRED = 5
    WRONG_DATA = 6
    FAILED = 7

    CHOICES = (
        (NEW, 'New'),
        (SUCCESS, 'Success'),
        (WRONG_PIN, 'Wrong PIN'),
        (CANCEL, 'Canceled'),
        (WRONG_NUMBER, 'Wrong number'),
        (WRONG_DATA, 'Wrong data'),
        (EXPIRED, 'Expired'),
        (FAILED, 'Failed'),
    )


class MPesaTransaction(models.Model):
    """
    Store MPesa transaction data
    """
    created_at = models.DateTimeField(
        verbose_name='created at', auto_now_add=True
    )
    transaction_type = models.IntegerField(
        verbose_name='transaction type',
        choices=TransactionType.CHOICES
    )
    amount = models.DecimalField(
        verbose_name='amount',
        max_digits=10,
        decimal_places=2
    )
    party_a = models.CharField(verbose_name='party A', max_length=100)
    party_b = models.CharField(verbose_name='party B', max_length=100)
    phone_number = models.CharField(verbose_name='phone number', max_length=35)
    description = models.TextField(verbose_name='description')

    # response
    status = models.PositiveSmallIntegerField(
        verbose_name='status',
        choices=TransactionStatus.CHOICES,
        default=TransactionStatus.NEW
    )
    response_code = models.CharField(
        verbose_name='response code',
        choices=ResponseCode.CHOICES,
        max_length=5,
        blank=True
    )
    response_description = models.TextField(
        verbose_name='response description',
        blank=True
    )

    merchant_request_id = models.CharField(
        verbose_name='merchant request id',
        max_length=255,
        blank=True
    )
    checkout_request_id = models.CharField(
        verbose_name='checkout request id',
        max_length=255,
        blank=True
    )

    result_code = models.IntegerField(
        verbose_name='result code',
        null=True, blank=True
    )
    result_desc = models.TextField(
        verbose_name='result description',
        blank=True
    )

    customer_message = models.TextField(
        verbose_name='customer message',
        blank=True
    )
    response_data = models.TextField(
        verbose_name='response data',
        blank=True
    )
    callback_data = models.TextField(
        verbose_name='callback data',
        blank=True
    )

    def __str__(self):
        return 'Transaction from {} to {} on {}'.format(
            self.party_a, self.party_b, self.amount
        )

    def refund(self):
        """
        :return: refund payment
        """
        from apps.mpesa_gateway.gateway import MPesaGateway

        mg = MPesaGateway()
        mg.refund(self)

    @property
    def success(self):
        """
        https://developer.safaricom.co.ke/docs?python#m-pesa-result-codes
        :return: if transaction is success
        """
        return self.result_code == 0

    @property
    def status_verbose(self):
        return dict(TransactionStatus.CHOICES).get(self.status)

    def update_status(self):
        if 'Request cancelled by user' in self.result_desc:
            self.set_cancel()
        elif self.result_desc == 'The service request is processed successfully.':
            from apps.management.orders.models import Payment
            payment = Payment.objects.filter(transaction=self).last()
            self.set_success(payment)
        elif self.result_desc == 'The initiator information is invalid.':
            self.set_wrong_pin()
        else:
            self.set_wrong_data()

    def set_success(self, payment, commit=True):
        self.status = TransactionStatus.SUCCESS

        if commit:
            self.save()

    def set_fail(self, commit=True):
        self.status = TransactionStatus.FAILED

        if commit:
            self.save()

    def set_expired(self, commit=True):
        self.status = TransactionStatus.EXPIRED
        if commit:
            self.save()

    def set_cancel(self, commit=True):
        self.status = TransactionStatus.CANCEL
        if commit:
            self.save()

    def set_wrong_pin(self, commit=True):
        self.status = TransactionStatus.WRONG_PIN
        if commit:
            self.save()

    def set_wrong_data(self, commit=True):
        self.status = TransactionStatus.WRONG_DATA
        if commit:
            self.save()

    def set_wrong_number(self, commit=True):
        self.status = TransactionStatus.WRONG_NUMBER
        if commit:
            self.save()

    def check_timeout(self):
        seconds_after_created = (
                timezone.now() - self.created_at
        ).total_seconds()
        if self.status == TransactionStatus.NEW and \
                seconds_after_created > settings.MPESA_REQUEST_TIMEOUT:
            self.status = TransactionStatus.FAILED
            self.save()