# system
import json
import requests
import random
import logging
import datetime
from decimal import Decimal

# django
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db import models
from django.urls import reverse

# ofinta
from apps.core.mixins import ModelDiffMixin
from apps.core.models import OfintaUser
from apps.management.orders.constants import OrderStatus, PaymentMethod, \
    OrderAssignmentStatus, PaymentStatus, PushStatuses
from apps.management.orders.managers import OrderManager
from apps.management.shops.models import Shop
from apps.management.warehouses.models import Warehouse
from apps.mpesa_gateway.gateway import MPesaGateway
from apps.mpesa_gateway.models import MPesaTransaction, TransactionStatus
from apps.shared.models import Location


logger = logging.getLogger(__name__)


class Order(models.Model, ModelDiffMixin):
    """
    Stores order information
    """
    payment_link_id = models.CharField(
        verbose_name='payment link id',
        max_length=30, blank=True
    )
    verification_code = models.CharField(
        verbose_name='verification code',
        max_length=8, blank=True
    )
    order_number = models.BigIntegerField(
        verbose_name='order number',
        unique=True
    )
    status = models.PositiveSmallIntegerField(
        verbose_name='status',
        choices=OrderStatus.CHOICES,
        default=OrderStatus.NEW
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name='shop',
        related_name='orders',
        on_delete=models.CASCADE
    )
    driver = models.ForeignKey(
        OfintaUser,
        verbose_name='driver',
        related_name='orders',
        null=True, blank=True,
        on_delete=models.CASCADE
    )
    warehouse = models.ForeignKey(
        Warehouse,
        verbose_name='warehouse',
        on_delete=models.CASCADE,
        related_name='orders',
        null=True
    )
    shipping_address = models.OneToOneField(
        Location,
        verbose_name='shipping address',
        related_name='order_from_shipping',
        on_delete=models.CASCADE
    )
    delivery_fee = models.DecimalField(
        verbose_name='delivery fee',
        default=Decimal(0), decimal_places=2, max_digits=9
    )
    buyer_name = models.CharField(verbose_name='buyer name', max_length=128)
    buyer_phone = models.CharField(
        verbose_name='buyer phone',
        max_length=20,
        blank=True
    )
    buyer_email = models.EmailField(verbose_name='buyer email', blank=True)

    is_paid = models.BooleanField(verbose_name='order is paid', default=False)
    is_payment_link = models.BooleanField(
        verbose_name='order is payment link',
        default=False
    )

    verification_required = models.BooleanField(
        verbose_name='verification by code is required',
        default=False
    )
    pending_transaction = models.BooleanField(
        verbose_name='pending transaction',
        default=False
    )
    created_at = models.DateTimeField(
        verbose_name='created at',
        auto_now_add=True
    )
    completed_at = models.DateTimeField(
        verbose_name='completed at',
        blank=True, null=True
    )
    payment_method = models.PositiveIntegerField(
        verbose_name='payment method',
        choices=PaymentMethod.CHOICES,
        null=True, blank=True
    )
    comment = models.TextField(
        verbose_name='comment',
        max_length=2000,
        blank=True
    )

    objects = OrderManager()

    class Meta:
        ordering = ('-created_at', )

    def __str__(self):
        return (f'Order by {self.buyer_name} at {self.shop} '
                f'[{self.status_verbose}]')

    def get_transaction(self):
        try:
            payment = Payment.objects.get(order=self)
            return payment.transaction
        except Payment.DoesNotExist:
            return

    def send_push_to_assigned_driver(self, message, push_extra={}, driver=None):
        driver = driver or self.assigned_driver
        if not driver:
            return

        driver_profile = driver.driver_profile \
            if hasattr(driver, 'driver_profile') else None

        if not driver_profile:
            return

        driver_profile.send_push(message, push_extra, self)

    @property
    def is_valid(self):
        day_ago = timezone.now() - datetime.timedelta(days=1)

        if self.created_at < day_ago:
            return False

        if not self.is_payment_link:
            return False

        payment = self.payment if hasattr(self, 'payment') else None
        if not payment:
            return True

        txn = payment.txn
        paid = self.payment_method == PaymentMethod.MPESA \
               and txn.status != TransactionStatus.SUCCESS or \
               self.payment_method == PaymentMethod.CASH

        if paid:
            return True

        is_active = self.payment_link_id is not None and self.is_payment_link
        return is_active

    @property
    def payment_link(self):
        rel_url = reverse(
            'payment-link-edit', args=(self.payment_link_id, )
        )
        full_url = ''.join(
            ['http://', Site.objects.get_current().domain, rel_url]
        )
        return full_url

    @property
    def payment_ran_by_driver(self):
        return not self.verification_required \
               and self.status == OrderStatus.DELIVERED

    def save(self, *args, **kwargs):
        driver = self.assigned_driver
        super(Order, self).save(*args, **kwargs)

        diff_status = self.diff.get('status', [None, None])
        if diff_status == (
                OrderStatus.ASSIGNED,
                OrderStatus.CANCELED
        ):
            self.send_push_to_assigned_driver(
                message=None,
                push_extra={'status': PushStatuses.ORDER_REMOVED},
                driver=driver
            )
        elif diff_status[1] == OrderStatus.CANCELED:
            self.send_push_to_assigned_driver(
                message=None,
                push_extra={'status': PushStatuses.ORDER_CANCELED},
                driver=driver
            )

    @property
    def assigned_driver(self):

        if self.driver:
            return self.driver

        assignment = self.assignments.last()
        if not assignment:
            return

        if assignment.status == OrderAssignmentStatus.REJECTED:
            return

        return assignment.driver

    def paid_via_mpesa(self):
        if not hasattr(self, 'payment'):
            return False

        payment = getattr(self, 'payment')
        txn = payment.transaction
        return txn.status == TransactionStatus.SUCCESS

    def total_quantity(self):
        return sum([position.quantity for position in self.positions.all()])

    def total_price(self):
        return sum([
            position.quantity * position.price
            for position in self.positions.all()
        ]) + self.delivery_fee

    def new_refund(self):
        """
        Refund order payment
        """
        payment = self.payment
        txn = payment.transaction

        mg = MPesaGateway()
        result = mg.refund(txn)
        return result['success']

    def refund(self, reason):
        """
        Send refund request
        :param reason: refund reason
        """
        logger.warning(
            'Payment response data: {}'.format(self.payment.response_data)
        )
        try:
            uid = self.payment.response_data['transaction']['uid']
        except:
            response = {
                'status': 'failed',
                'message': 'Bad Request',
                'transaction': {'refund': {'status': 'failed'}}
            }
            logger.warning('Refund response: {}'.format(response))
            return response

        data = {
            'request': {
                "parent_uid": uid,
                "amount": int(self.total_price() * 100),
                "reason": reason
            }
        }
        logger.warning('Refund request: {}'.format(data))
        headers = {'content-type': 'application/json'}
        resp = requests.post(
            settings.API_REFUND_URL,
            data=json.dumps(data),
            headers=headers,
            auth=(settings.SHOP_ID, settings.SHOP_KEY)
        )
        return resp.json()

    def generate_verification_code(self):
        verification_code = random.randint(10000, 99999)
        self.verification_code = verification_code
        self.save()
        return verification_code

    def send_verification_code_by_email(self):
        """
        Send verification code to the buyer's email
        """
        subject = 'Your verification code'
        body = f"""New verification code for the order #{self.order_number}.\n\nOrder amount: {self.total_price()}\n\nCode: {self.verification_code}
        """
        send_mail(
            subject,
            body,
            settings.NOTIFICATIONS_EMAIL,
            [self.buyer_email]
        )

    def send_verification_code_by_sms(self):
        """
        Send verification code to the buyer's phone
        """
        try:
            import africastalking
            africastalking.initialize(settings.SMS_USERNAME, settings.SMS_API_KEY)
            sms = africastalking.SMS
            sms.send(
                "Your verification code is: {}".format(self.verification_code),
                [self.get_phone_number(with_plus=True)]
            )
        except Exception as e:
            logger.exception(e)

    def get_phone_number(self, with_plus):
        if with_plus:
            if self.buyer_phone.startswith('+'):
                return self.buyer_phone
            else:
                return '+{}'.format(self.buyer_phone)
        else:
            if self.buyer_phone.startswith('+'):
                return self.buyer_phone[1:]
            else:
                return self.buyer_phone

    @property
    def is_active(self):
        return not self.is_canceled and not self.is_completed

    @property
    def is_canceled(self):
        return self.status == OrderStatus.CANCELED

    @property
    def is_delivered(self):
        return self.status == OrderStatus.DELIVERED

    @property
    def is_completed(self):
        return self.status == OrderStatus.COMPLETED

    def get_absolute_url(self):
        return reverse('management:order-details', args=(self.pk, ))

    @property
    def status_verbose(self):
        return dict(OrderStatus.CHOICES)[self.status]

    @property
    def payment_method_verbose(self):
        return dict(PaymentMethod.CHOICES).get(self.payment_method, 'N/A')

    def set_processed(self, commit=True):
        self.status = OrderStatus.PROCESSED
        if commit:
            self.save()

    def set_canceled(self, commit=True):
        self.status = OrderStatus.CANCELED
        if commit:
            self.save()

    def set_delivered(self, commit=True):
        self.status = OrderStatus.DELIVERED
        if commit:
            self.save()

    def set_completed(self, commit=True):
        self.status = OrderStatus.COMPLETED
        self.completed_at = timezone.now()
        if commit:
            self.save()

    def set_paid(self, commit=True):
        self.is_paid = True
        if commit:
            self.save()


class OrderAssignments(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='order',
        related_name='assignments',
        on_delete=models.CASCADE
    )
    driver = models.ForeignKey(
        OfintaUser,
        verbose_name='driver',
        related_name='assignments',
        on_delete=models.CASCADE
    )
    status = models.PositiveIntegerField(
        verbose_name='status',
        choices=OrderAssignmentStatus.CHOICES,
        default=OrderAssignmentStatus.ASSIGNED
    )

    def __str__(self):
        return f'Order {self.order.order_number} assignment to ' \
               f'{self.driver}. Status: {self.status_verbose}'

    @property
    def status_verbose(self):
        return dict(OrderAssignmentStatus.CHOICES)[self.status]


class Position(models.Model):
    """
    Stores product position data from customer's shop
    """
    order = models.ForeignKey(
        Order,
        verbose_name='order',
        related_name='positions',
        on_delete=models.CASCADE
    )
    item_id = models.CharField(verbose_name='item id', max_length=255)
    name = models.CharField(verbose_name='name', max_length=255)
    quantity = models.PositiveIntegerField(
        verbose_name='quantity', default=1, validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        verbose_name='price',
        decimal_places=2, max_digits=10
    )
    currency = models.CharField(
        verbose_name='currency',
        max_length=5, default='KES'
    )

    def __str__(self):
        return f'(id: {self.item_id}) {self.name}'


class Payment(models.Model):

    order = models.OneToOneField(
        Order,
        verbose_name='Order',
        related_name='payment',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        verbose_name='Creation date',
        default=timezone.now
    )
    processed_at = models.DateTimeField(
        verbose_name='Processed date',
        null=True, blank=True
    )
    transaction = models.ForeignKey(
        MPesaTransaction,
        verbose_name='transaction',
        related_name='payment',
        null=True, blank=True,
        on_delete=models.CASCADE
    )

    @property
    def status_verbose(self):
        return dict(PaymentStatus.CHOICES).get(self.status)

    def new_submit(self):
        """
        Submit payment
        """
        gw = MPesaGateway()
        phone_number = self.order.get_phone_number(with_plus=False)
        result = gw.payment(
            self,
            self.order.total_price(),
            phone_number,
            'payment'
        )
        success = result['success']
        transaction = result.get('transaction')
        if success:
            self.order.pending_transaction = True
            self.order.save()

            self.transaction = transaction
            self.save()
        else:
            self.order.send_push_to_assigned_driver(
                message=None,
                push_extra={
                    "status": PushStatuses.ORDER_PAY_FAILED,
                    "code": transaction.response_code,
                    "description": transaction.response_description
                },
            )

        return success
