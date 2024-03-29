# system
import os
import binascii
import random

# django
from django.conf import settings

# third party
import factory
from factory.fuzzy import FuzzyChoice

# ofinta
from apps.core.models import UserRoles
from apps.management.drivers.models import DriverProfile
from apps.mpesa_gateway.models import MPesaTransaction, TransactionType
from apps.shared.models import Location
from apps.management.shops.models import Shop
from apps.management.warehouses.models import Warehouse
from apps.management.orders.constants import PaymentMethod, PaymentStatus
from apps.management.orders.models import Order, Payment

ADDRESSES = [
    'Yaya Centre, Mbagathi Rd, Hurlingham',
    'Reinsurance Plaza, 7th Flr Taifa Rd, 56653-00200 City Square',
    'Nakuru/Nairobi Hwy, P.O. Box: 9579-20100 Nakuru',
    'Echo Service Centre, Kitui Rd',
    'Thika Arcadetta Hwy, Box 4380-01000',
    'Parklands Sports Club, Ojijo Rd, Parklands',
    'Sasio Rd off Lunga Lunga Rd'
]


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    address = FuzzyChoice(ADDRESSES)


class ShopFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Shop

    name = factory.Sequence(lambda n: f'shop {n}')
    api_key = factory.Sequence(
        lambda n: binascii.hexlify(os.urandom(20)).decode()
    )


class WarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Warehouse

    shop = factory.SubFactory(ShopFactory)
    name = factory.Sequence(lambda n: f'warehouse_{n}')
    location = factory.SubFactory(LocationFactory)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    email = factory.Sequence(lambda n: f'user_{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password')


class DriverFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    role = UserRoles.DRIVER
    first_name = factory.Sequence(lambda n: f'first_name_{n}')
    last_name = factory.Sequence(lambda n: f'last_name_{n}')
    email = factory.Sequence(lambda n: f'driver_{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password')


class DriverProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DriverProfile

    user = factory.SubFactory(DriverFactory)
    phone = factory.Sequence(lambda n: f'123-45-67')
    driver_id = factory.Sequence(lambda n: f'driver-id-{n}')
    bike_registration = factory.Sequence(lambda n: f'registration-{n}')


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    order_number = factory.Sequence(
        lambda n: random.randint(1000, 10000)
    )
    shop = factory.SubFactory(ShopFactory)
    driver = factory.SubFactory(DriverFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    shipping_address = factory.SubFactory(LocationFactory)
    delivery_fee = factory.Sequence(
        lambda n: random.randint(1, 10000)
    )
    buyer_name = factory.Sequence(lambda n: f'buyer {n}')
    buyer_phone = factory.Sequence(lambda n: '123-45-67')
    buyer_email = factory.Sequence(lambda n: f'email_{n}.example.com')
    payment_method = PaymentMethod.MPESA


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)


class TransactionFactory(factory.django.DjangoModelFactory):
    transaction_type = TransactionType.PAYMENT
    party_a = factory.Sequence(lambda n: f'party_a_{n}')
    party_b = factory.Sequence(lambda n: f'party_b_{n}')
    phone_number = '+380685978789'
    description = factory.Sequence(lambda n: f'desc_{n}')
    amount = factory.Sequence(lambda n: random.randint(1, 10))

    class Meta:
        model = MPesaTransaction
