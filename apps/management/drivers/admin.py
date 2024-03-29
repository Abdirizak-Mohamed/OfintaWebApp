# django
from django.contrib import admin

# ofinta
from apps.management.drivers.models import DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone',
        'driver_id',
        'bike_registration',
        'last_update'
    )
    fields = (
        'user', 'phone', 'driver_id', 'bike_registration', 'coordinates',
        'last_update', 'photo'
    )
    readonly_fields = ('last_update', )
