# django
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = 'apps.management.orders'

    def ready(self):
        from apps.management.warehouses.signals import generate_code
        from django.db.models.signals import pre_save
        from apps.management.warehouses.models import Warehouse
        from apps.management.orders.models import Order
        from apps.management.warehouses.signals import generate_order_number

        pre_save.connect(
            generate_code,
            sender=Warehouse,
            dispatch_uid='warehouse_created'
        )
        pre_save.connect(
            generate_order_number,
            sender=Order,
            dispatch_uid='order_pre_create'
        )
