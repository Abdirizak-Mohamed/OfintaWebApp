# system
import os
import binascii
import logging

# django
from django import forms
from django.utils import timezone

# ofinta
from django.contrib.gis.geos import Point
from django.db.models.aggregates import Max
from django.forms.models import inlineformset_factory
from django.forms.widgets import HiddenInput

from apps.core.models import OfintaUser, UserRoles
from apps.core.utils import get_coordinates_by_address
from apps.management.orders.constants import OrderStatus, \
    OrderAssignmentStatus, PushStatuses, PaymentMethod
from apps.management.orders.models import Order, OrderAssignments, Position, \
    Payment
from apps.shared.models import Location


logger = logging.getLogger(__name__)


class OrderEditForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = (
            'warehouse', 'buyer_name', 'buyer_phone', 'payment_method'
        )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shop = user.shop
        self.fields['warehouse'].queryset = shop.warehouses.all()


class PaymentLinkEditForm(forms.ModelForm):

    pay = forms.CharField(required=False)

    class Meta:
        model = Order
        fields = (
            'buyer_name', 'buyer_phone', 'buyer_email', 'payment_method', 'pay'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['buyer_name'].label = 'Name'
        self.fields['buyer_phone'].label = 'Phone'
        self.fields['buyer_email'].label = 'Email'

        self.fields['pay'].widget = HiddenInput()

    def save(self, commit=False):
        order = super().save(commit)

        order.status = OrderStatus.NEW
        order.confirmed = True
        order.save()

        # remove previous payments for the order
        Payment.objects.filter(order=order).delete()

        pay = bool(self.cleaned_data.get('pay'))
        able_to_pay = pay and order.shop.allow_prepayment

        # create new payment
        if order.payment_method == PaymentMethod.MPESA:
            if able_to_pay:
                payment = Payment.objects.create(order=order)
                payment.new_submit()

        order.save()
        return order


class PaymentLinkCancelForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ('status', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['status'].widget = HiddenInput()

    def save(self, commit=False):
        order = super().save(commit=False)
        order.status = OrderStatus.CANCELED
        order.save()
        return order


class PaymentLinkCreateForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = (
            'shop', 'order_number', 'warehouse',
            'buyer_name', 'buyer_phone', 'buyer_email',
            'payment_method', 'delivery_fee', 'comment'
        )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shop = user.shop
        self.fields['shop'].initial = shop.id
        self.fields['shop'].widget = HiddenInput()

        max_order_number = Order.objects.all().aggregate(
            Max('order_number')
        )['order_number__max']
        
        self.fields['order_number'].initial = max_order_number + 1 if max_order_number else 1

        self.fields['warehouse'].empty_label = None
        self.fields['warehouse'].queryset = shop.warehouses.all()
        last_order = shop.orders.filter(warehouse__isnull=False).last()
        if last_order:
            self.fields['warehouse'].initial = last_order.warehouse

        self.fields['buyer_name'].label = 'Name'
        self.fields['buyer_phone'].label = 'Phone'
        self.fields['buyer_email'].label = 'Email'

        self.fields['payment_method'].initial = PaymentMethod.CASH
        self.fields['delivery_fee'].initial = shop.default_delivery_fee

        self.fields['comment'].widget = forms.Textarea(attrs={'rows': 2})

    def save(self, commit=False):
        order = super().save(commit=False)
        order.payment_link_id = binascii.hexlify(os.urandom(5)).decode('utf-8')
        order.is_payment_link = True
        return order


class PaymentLinkPositionForm(forms.ModelForm):

    class Meta:
        models = Position
        fields = (
            'item_id', 'name', 'quantity', 'price'
        )


OrderPositionFormSet = inlineformset_factory(
    Order, Position,
    form=PaymentLinkPositionForm, extra=0,
    min_num=1, validate_min=True
)


class OrderShippingAddressForm(forms.ModelForm):

    class Meta:
        model = Location
        fields = ('address', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].label = 'Shipping address'

    def clean_address(self):
        
        address = self.cleaned_data['address']

        if address:
            lat, lng = get_coordinates_by_address(address)
            if not lat and not lng:
                raise forms.ValidationError('Address should be a valid google maps address')

        return address

    def save(self, commit=True):

        location = super().save(commit)
        address = location.address
        if address:
            lat, lng = get_coordinates_by_address(address)
            location.coordinates = Point(lat, lng)
            location.save()
        return location


class OrderCancelForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ()

    def save(self, commit=True):
        order = super().save(commit)
        if order.paid_via_mpesa():
            success = order.new_refund()
            if not success:
                return order

        order.status = OrderStatus.CANCELED
        order.completed_at = timezone.now()
        order.save()
        return order


class OrderSearchForm(forms.Form):

    order_number = forms.CharField(required=False)
    start_date = forms.DateField(label='Date range start', required=False)
    end_date = forms.DateField(label='Date range end', required=False)

    class Meta:
        fields = (
            'order_number', 'start_date', 'end_date'
        )


class DriverAssignForm(forms.ModelForm):

    class Meta:
        model = OrderAssignments
        fields = ('driver', )

    def __init__(self, order, *args, **kwargs):
        self.order = order
        super().__init__(*args, **kwargs)
        drivers_qset = OfintaUser.objects.filter(
            role=UserRoles.DRIVER,
            shop=self.order.shop
        )
        if self.order.assigned_driver:
            drivers_qset = drivers_qset.exclude(
                id=self.order.assigned_driver.id
            )
        self.fields['driver'].queryset = drivers_qset

    def save(self, commit=True):
        # remove previous assigned assignments
        prev_assignments = self.order.assignments.filter(
            status__in=[OrderAssignmentStatus.ASSIGNED,
                        OrderAssignmentStatus.ACCEPTED]
        )

        # send push notification to the previous drivers
        for prev_assignment in prev_assignments:
            prev_driver_profile = prev_assignment.driver.driver_profile
            prev_driver_profile.send_push(
                None,
                {"status": PushStatuses.ORDER_REASSIGNED},
                self.order
            )

        prev_assignments.delete()

        assignment = super().save(False)
        assignment.order = self.order
        assignment.save()

        # send push notification to the new driver
        driver_profile = assignment.driver.driver_profile \
            if hasattr(assignment.driver, 'driver_profile') else None
        if driver_profile:
            driver_profile.send_push(
                None,
                {"status": PushStatuses.ORDER_ASSIGNED},
                self.order
            )

        self.order.status = OrderStatus.ASSIGNED
        self.order.driver = None

        self.order.save()
        return assignment
