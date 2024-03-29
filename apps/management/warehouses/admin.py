# django
from django.contrib import admin

# ofinta
from apps.management.warehouses.models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    """
    Warehouse model admin
    """
    list_display = ('name', 'code', 'shop')
