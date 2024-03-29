# system
import datetime

# third party
import pytest
from pytest_mock import mocker

# django
from django.urls import reverse
from django.utils import timezone

# ofinta
from apps.management.dashboard.tests.factories import OrderFactory, \
    ShopFactory, WarehouseFactory, DriverFactory, PaymentFactory, \
    TransactionFactory
from apps.management.orders.constants import OrderStatus, PaymentMethod, \
    OrderAssignmentStatus, PaymentStatus
from apps.management.orders.models import OrderAssignments, Order
from apps.mpesa_gateway.models import TransactionStatus


@pytest.mark.django_db
class TestOrders:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self, manager):
        # shop 1
        self.shop_1 = ShopFactory()

        self.manager = manager
        self.manager.shop = self.shop_1
        self.manager.save()

        # active orders
        self.warehouse_1_1 = WarehouseFactory(shop=self.shop_1)
        self.warehouse_1_2 = WarehouseFactory(shop=self.shop_1)
        self.active_order_1_1 = OrderFactory(
            shop=self.shop_1,
            order_number=1,
            status=OrderStatus.ACCEPTED,
            driver=None,
            warehouse=self.warehouse_1_1
        )
        self.txn_1_1 = TransactionFactory(status=TransactionStatus.SUCCESS)
        self.payment_1_1 = PaymentFactory(
            order=self.active_order_1_1,
            transaction=self.txn_1_1
        )
        self.active_order_1_2 = OrderFactory(
            shop=self.shop_1,
            order_number=2,
            status=OrderStatus.ASSIGNED,
            driver=None,
            warehouse=self.warehouse_1_2
        )

        # recent orders
        self.recent_order_1_1 = OrderFactory(
            shop=self.shop_1,
            order_number=3,
            status=OrderStatus.CANCELED,
            driver=None,
            warehouse=self.warehouse_1_1
        )
        self.recent_order_1_2 = OrderFactory(
            shop=self.shop_1,
            order_number=4,
            status=OrderStatus.COMPLETED,
            driver=None,
            warehouse=self.warehouse_1_1
        )

        # shop 2
        self.shop_2 = ShopFactory()

        self.warehouse_2_1 = WarehouseFactory(shop=self.shop_2)
        self.warehouse_2_2 = WarehouseFactory(shop=self.shop_2)

        # active orders (shop 2)
        self.active_order_2_1 = OrderFactory(
            shop=self.shop_2,
            order_number=5,
            status=OrderStatus.ASSIGNED,
            driver=None,
            warehouse=self.warehouse_2_2
        )

        # recent orders (shop 2)
        self.recent_order_2_1 = OrderFactory(
            shop=self.shop_2,
            order_number=6,
            status=OrderStatus.COMPLETED,
            driver=None,
            warehouse=self.warehouse_2_1
        )

    def test_orders_search(self, client, manager):
        url = reverse('management:orders-list')

        client.login(email=manager.email, password='password')

        response = client.get(url)
        context = response.context
        assert self.active_order_1_1 in context['orders']

        # 2nd order has no success payment
        assert self.active_order_1_2 not in context['orders']
        assert len(context['orders']) == 1

        # search by `order_number`
        search_url = '{}?order_number=1'.format(url)
        response = client.get(search_url)
        context = response.context
        assert self.active_order_1_1 in context['orders']
        assert len(context['orders']) == 1

        search_url = '{}?order_number=3'.format(url)
        response = client.get(search_url)
        context = response.context
        assert len(context['orders']) == 0

        # search by date`
        now = timezone.now()
        self.active_order_1_1.created_at = now - datetime.timedelta(days=4)
        self.active_order_1_1.save()
        self.active_order_1_2.created_at = now - datetime.timedelta(days=6)
        self.active_order_1_2.save()

        five_days_ago = now - datetime.timedelta(days=5)
        search_url = '{}?start_date={}%2F{}%2F{}'.format(
            url, five_days_ago.month, five_days_ago.day, five_days_ago.year
        )
        response = client.get(search_url)
        context = response.context
        assert self.active_order_1_1 in context['orders']
        assert len(context['orders']) == 1

        five_days_ago = now - datetime.timedelta(days=3)
        search_url = '{}?end_date={}%2F{}%2F{}'.format(
            url, five_days_ago.month, five_days_ago.day, five_days_ago.year
        )
        response = client.get(search_url)
        context = response.context
        assert self.active_order_1_1 in context['orders']
        assert len(context['orders']) == 1

    def test_orders_list(self, client, manager):
        url = reverse('management:orders-list')

        client.login(email=manager.email, password='password')

        response = client.get(url)
        context = response.context
        assert self.active_order_1_1 in context['orders']

        # 2nd oder has no success payment
        assert self.active_order_1_2 not in context['orders']
        assert len(context['orders']) == 1

    def test_orders_history(self, client, manager):
        url = reverse('management:orders-history')

        client.login(email=manager.email, password='password')

        response = client.get(url)
        context = response.context
        assert self.recent_order_1_1 in context['orders']
        assert self.recent_order_1_2 in context['orders']
        assert len(context['orders']) == 2

    def test_order_details(self, client, manager):
        url = reverse(
            'management:order-details',
            args=(self.active_order_1_1.pk, )
        )

        client.login(email=manager.email, password='password')

        response = client.get(url)
        assert response.status_code == 200
        context = response.context
        assert self.active_order_1_1 == context['order']

        # manager has no access to the other shops orders
        url = reverse(
            'management:order-details', args=(self.active_order_2_1.pk,)
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_order_edit(self, client):
        url = reverse(
            'management:order-edit', args=(self.active_order_1_1.pk,)
        )

        client.login(email=self.manager.email, password='password')

        post_data = {
            'warehouse': self.warehouse_1_2.pk,
            'buyer_name': 'New buyer',
            'buyer_phone': '+25420828734',
            'payment_method': PaymentMethod.CASH
        }
        response = client.post(url, post_data)
        assert response.status_code == 302
        assert response.url == reverse(
            'management:order-details', args=(self.active_order_1_1.pk,)
        )
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.warehouse == self.warehouse_1_2

        # manager cannot edit orders of the shops where he is not manager
        url = reverse(
            'management:order-edit', args=(self.active_order_2_1.pk,)
        )
        post_data['warehouse'] = self.warehouse_2_1.pk
        response = client.post(url, post_data)
        assert response.status_code == 404

    def test_driver_assign(self, client):
        url = reverse(
            'management:driver-assign', args=(self.active_order_1_1.pk,)
        )

        # create one driver for each shop
        self.driver_1_1 = DriverFactory(shop=self.shop_1)
        self.driver_2_1 = DriverFactory(shop=self.shop_2)

        client.login(email=self.manager.email, password='password')

        # manager cannot assign to the order driver from the other shop
        assignments_before = OrderAssignments.objects.count()
        post_data = {'driver': self.driver_2_1.pk}
        response = client.post(url, post_data)
        assert response.status_code == 200
        assert response.context['form'].is_valid() is False
        assert OrderAssignments.objects.count() == assignments_before

        # assign driver from the correct shop
        assignments_before = OrderAssignments.objects.count()
        post_data = {'driver': self.driver_1_1.pk}
        response = client.post(url, post_data)
        assert response.status_code == 302
        assert response.url == reverse(
            'management:order-details', args=(self.active_order_1_1.pk,)
        )
        assert OrderAssignments.objects.count() == assignments_before + 1
        order_assignment = OrderAssignments.objects.first()
        assert order_assignment.driver == self.driver_1_1
        assert order_assignment.order == self.active_order_1_1
        assert order_assignment.status == OrderAssignmentStatus.ASSIGNED

        # manager cannot edit orders of the shops where he is not manager
        url = reverse(
            'management:driver-assign', args=(self.active_order_2_1.pk,)
        )
        post_data['driver'] = self.driver_2_1.pk
        response = client.post(url, post_data)
        assert response.status_code == 404

    def test_order_cancel_cash(self, client, mocker):
        """
        Test order paid with cash cancel
        """
        mocker.patch('apps.management.orders.models.Order.new_refund')
        Order.refund_value = {}
        assert Order.new_refund.called is False

        url = reverse(
            'management:order-cancel', args=(self.active_order_1_1.pk,)
        )

        client.login(email=self.manager.email, password='password')

        response = client.post(url, {})
        assert response.status_code == 302
        assert response.url == reverse(
            'management:order-details', args=(self.active_order_1_1.pk,)
        )
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.CANCELED

        # manager cannot edit orders of the shops where he is not manager
        url = reverse(
            'management:order-cancel', args=(self.active_order_2_1.pk,)
        )
        response = client.post(url, {})
        assert response.status_code == 404

    def test_order_cancel_mpesa_new(self, client, mocker):
        """
        Test new order with mpesa cancel
        """
        mocker.patch('apps.management.orders.models.Order.new_refund')
        Order.refund_value = {}
        assert Order.new_refund.called is False

        url = reverse(
            'management:order-cancel', args=(self.active_order_1_1.pk,)
        )

        client.login(email=self.manager.email, password='password')

        response = client.post(url, {})
        assert response.status_code == 302
        assert response.url == reverse(
            'management:order-details', args=(self.active_order_1_1.pk,)
        )
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.CANCELED

        # manager cannot edit orders of the shops where he is not manager
        url = reverse(
            'management:order-cancel', args=(self.active_order_2_1.pk,)
        )
        response = client.post(url, {})
        assert response.status_code == 404

    def test_order_cancel_mpesa_paid(self, client, mocker):
        """
        Test paid order with mpesa cancel
        """
        mocker.patch('apps.management.orders.models.Order.new_refund')
        Order.refund_value = {}

        url = reverse(
            'management:order-cancel', args=(self.active_order_1_1.pk,)
        )

        client.login(email=self.manager.email, password='password')

        response = client.post(url, {})
        assert response.status_code == 302
        assert response.url == reverse(
            'management:order-details', args=(self.active_order_1_1.pk,)
        )

        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.CANCELED
        Order.new_refund.assert_called_once_with()

        # manager cannot edit orders of the shops where he is not manager
        url = reverse(
            'management:order-cancel', args=(self.active_order_2_1.pk,)
        )
        response = client.post(url, {})
        assert response.status_code == 404
