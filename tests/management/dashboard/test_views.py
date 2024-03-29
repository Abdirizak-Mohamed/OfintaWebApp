
# third party
import pytest

# ofinta
from django.urls import reverse

# define fixtures
from apps.management.dashboard.tests.factories import OrderFactory, ShopFactory, \
    DriverFactory, WarehouseFactory, DriverProfileFactory, TransactionFactory
from apps.management.orders.constants import OrderStatus, PaymentStatus
from apps.management.orders.models import Payment
from apps.mpesa_gateway.models import TransactionStatus


@pytest.mark.django_db
class TestDashboard:
    pytestmark = pytest.mark.django_db

    def test_dashboard_manager(self, client, manager):
        url = reverse('management:dashboard')
        shop_1 = ShopFactory()
        manager.shop = shop_1
        manager.save()
        client.login(email=manager.email, password='password')

        # active orders
        active_order_1, active_order_2 = \
            OrderFactory(shop=shop_1), OrderFactory(shop=shop_1)
        active_order_1.status = OrderStatus.ACCEPTED

        active_order_1.save()
        active_order_2.status = OrderStatus.ASSIGNED
        active_order_2.save()
        Payment.objects.create(
            order=active_order_1,
            transaction=TransactionFactory(status=TransactionStatus.SUCCESS)
        )
        Payment.objects.create(
            order=active_order_2,
            transaction=TransactionFactory(status=TransactionStatus.SUCCESS)
        )

        # recent orders
        recent_order_1, recent_order_2 = \
            OrderFactory(shop=shop_1), OrderFactory(shop=shop_1)
        recent_order_1.status = OrderStatus.CANCELED
        recent_order_1.save()
        recent_order_2.status = OrderStatus.COMPLETED
        recent_order_2.save()

        # drivers
        driver_1, driver_2 = \
            DriverFactory(shop=shop_1), DriverFactory(shop=shop_1)

        DriverProfileFactory(user=driver_1)
        DriverProfileFactory(user=driver_2)

        # warehouses
        warehouse_1, warehouse_2 = \
            WarehouseFactory(shop=shop_1), WarehouseFactory(shop=shop_1)

        # shop 2
        shop_2 = ShopFactory()

        # active orders (shop 2)
        OrderFactory(shop=shop_2, status=OrderStatus.CANCELED)

        # recent orders (shop 2)
        OrderFactory(shop=shop_2)

        # drivers (shop 2)
        DriverFactory(shop=shop_2)
        DriverFactory(shop=shop_2)

        # warehouses (shop 2)
        WarehouseFactory(shop=shop_2)
        WarehouseFactory(shop=shop_2)

        response = client.get(url)
        context = response.context

        assert active_order_1 in context['active_orders']
        assert active_order_2 in context['active_orders']
        assert len(context['active_orders']) == 2

        assert recent_order_1 in context['recent_orders']
        assert recent_order_2 in context['recent_orders']
        assert len(context['recent_orders']) == 2

        assert driver_1 in context['active_drivers']
        assert driver_2 in context['active_drivers']
        assert len(context['active_drivers']) == 2

        assert warehouse_1 in context['warehouses']
        assert warehouse_2 in context['warehouses']
        assert len(context['warehouses']) == 2

        assert 'managers' not in context
        assert response.status_code == 200

    def test_dashboard_owner(self, client, manager, owner):
        url = reverse('management:dashboard')
        shop_1 = ShopFactory()
        manager.shop = shop_1
        manager.save()
        owner.save()
        owner.shop = shop_1
        owner.save()

        client.login(email=owner.email, password='password')

        # active orders
        active_order_1, active_order_2 = \
            OrderFactory(shop=shop_1), OrderFactory(shop=shop_1)
        active_order_1.status = OrderStatus.ACCEPTED
        active_order_1.save()

        Payment.objects.create(
            order=active_order_1,
            transaction=TransactionFactory(status=TransactionStatus.SUCCESS)
        )
        active_order_2.status = OrderStatus.ASSIGNED
        active_order_2.save()

        Payment.objects.create(
            order=active_order_2,
            transaction=TransactionFactory(status=TransactionStatus.SUCCESS)
        )

        # recent orders
        recent_order_1, recent_order_2 = \
            OrderFactory(shop=shop_1), OrderFactory(shop=shop_1)
        recent_order_1.status = OrderStatus.CANCELED
        recent_order_1.save()
        recent_order_2.status = OrderStatus.COMPLETED
        recent_order_2.save()

        # drivers
        driver_1, driver_2 = \
            DriverFactory(shop=shop_1), DriverFactory(shop=shop_1)

        DriverProfileFactory(user=driver_1)
        DriverProfileFactory(user=driver_2)

        # warehouses
        warehouse_1, warehouse_2 = \
            WarehouseFactory(shop=shop_1), WarehouseFactory(shop=shop_1)

        # shop 2
        shop_2 = ShopFactory()

        # active orders (shop 2)
        OrderFactory(shop=shop_2, status=OrderStatus.CANCELED)

        # recent orders (shop 2)
        OrderFactory(shop=shop_2)

        # drivers (shop 2)
        DriverFactory(shop=shop_2)
        DriverFactory(shop=shop_2)

        # warehouses (shop 2)
        WarehouseFactory(shop=shop_2)
        WarehouseFactory(shop=shop_2)

        response = client.get(url)
        context = response.context

        assert active_order_1 in context['active_orders']
        assert active_order_2 in context['active_orders']
        assert len(context['active_orders']) == 2

        assert recent_order_1 in context['recent_orders']
        assert recent_order_2 in context['recent_orders']
        assert len(context['recent_orders']) == 2

        assert driver_1 in context['active_drivers']
        assert driver_2 in context['active_drivers']
        assert len(context['active_drivers']) == 2

        assert warehouse_1 in context['warehouses']
        assert warehouse_2 in context['warehouses']
        assert len(context['warehouses']) == 2

        assert manager in context['managers']
        assert len(context['managers']) == 1

        assert response.status_code == 200
