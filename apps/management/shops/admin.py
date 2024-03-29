# django
from django.contrib import admin

# ofinta
from apps.management.shops.models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """
    Shop model admin
    """
    list_display = ('api_key', 'name', )
