# system
import json

# django
from django.conf import settings

# third party
import pytest

from apps.management.dashboard.tests.factories import OrderFactory, ShopFactory, \
    DriverProfileFactory
from apps.management.orders.constants import OrderStatus, PushStatuses
from apps.management.orders.models import Payment
from apps.mpesa_gateway.gateway import MPesaGateway
from apps.mpesa_gateway.models import MPesaTransaction, TransactionStatus, \
    TransactionType


@pytest.mark.django_db
class TestGateway:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self, manager):
        self.gw = MPesaGateway()

        self.shop = ShopFactory()
        self.order = OrderFactory(
            shop=self.shop,
            order_number=1,
            verification_code='ver_code'
        )
        self.order.pending_transaction = True
        self.order.save()

        self.driver = self.order.assigned_driver
        self.driver_profile = DriverProfileFactory(user=self.driver)

        self.payment = Payment.objects.create(order=self.order)

    def test_payment_by_buyer(self, mocker):
        """
        Test MPesaGateway payment
        """
        mocker.patch(
            'apps.management.orders.models.Order.send_verification_code_by_email'
        )
        mocker.patch(
            'apps.management.orders.models.Order.send_verification_code_by_sms'
        )
        send_push_mock = mocker.patch(
            'apps.management.drivers.models.DriverProfile.send_push'
        )
        gateway_payment_post_mock = mocker.patch('requests.post')
        gateway_payment_get_mock = mocker.patch('requests.get')
        res = self.gw.payment(
            payment=self.payment, amount=1, phone_number='1234567'
        )

        assert settings.MPESA_TEST_MODE is True
        assert settings.MPESA_TEST_RESPONSE_STATUS_CODE == 200

        txn = MPesaTransaction.objects.first()
        assert txn.transaction_type == TransactionType.PAYMENT
        assert txn.amount == 1
        assert txn.party_a == '1234567'
        assert txn.party_b == settings.MPESA_BUSINESS_SHORT_CODE
        assert txn.response_data == json.dumps(
            settings.MPESA_TEST_RESPONSE_200_JSON
        )

        # after webhook processed
        assert txn.status == TransactionStatus.SUCCESS
        self.order.refresh_from_db()
        assert self.order.is_paid is True
        assert self.order.pending_transaction is False

        assert gateway_payment_post_mock.called is False
        assert gateway_payment_get_mock.called is False
        assert send_push_mock.called is False
        assert res == {'success': True, 'transaction': txn}

    def test_payment_by_driver(self, mocker):
        """
        Test MPesaGateway payment
        """
        self.order.verification_required = False
        self.order.status = OrderStatus.DELIVERED
        self.order.save()

        mocker.patch(
            'apps.management.orders.models.Order.send_verification_code_by_email'
        )
        mocker.patch(
            'apps.management.orders.models.Order.send_verification_code_by_sms'
        )
        send_push_mock = mocker.patch(
            'apps.management.drivers.models.DriverProfile.send_push'
        )

        gateway_payment_post_mock = mocker.patch('requests.post')
        gateway_payment_get_mock = mocker.patch('requests.get')
        res = self.gw.payment(
            payment=self.payment, amount=1, phone_number='1234567'
        )

        assert settings.MPESA_TEST_MODE is True
        assert settings.MPESA_TEST_RESPONSE_STATUS_CODE == 200

        txn = MPesaTransaction.objects.first()
        assert txn.transaction_type == TransactionType.PAYMENT
        assert txn.amount == 1
        assert txn.party_a == '1234567'
        assert txn.party_b == settings.MPESA_BUSINESS_SHORT_CODE
        assert txn.response_data == json.dumps(
            settings.MPESA_TEST_RESPONSE_200_JSON
        )

        # after webhook processed
        assert txn.status == TransactionStatus.SUCCESS
        self.order.refresh_from_db()
        assert self.order.is_paid is True
        assert self.order.completed_at is not None
        assert self.order.pending_transaction is False

        assert gateway_payment_post_mock.called is False
        assert gateway_payment_get_mock.called is False
        assert send_push_mock.called is True
        send_push_mock.assert_called_once_with(
            None,
            {'status': PushStatuses.ORDER_PAY_SUCCEED},
            self.order
        )
        assert res == {'success': True, 'transaction': txn}
