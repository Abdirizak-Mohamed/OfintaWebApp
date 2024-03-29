from django.apps import AppConfig


class WarehousesConfig(AppConfig):
    name = 'apps.management.warehouses'

    def ready(self):
        from apps.management.warehouses.signals import generate_code
        from django.db.models.signals import pre_save
        from apps.management.warehouses.models import Warehouse
        pre_save.connect(
            generate_code,
            sender=Warehouse,
            dispatch_uid='warehouse_created'
        )
