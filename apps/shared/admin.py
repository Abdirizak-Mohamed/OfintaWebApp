# django
from django.contrib import admin

# ofinta
from mapwidgets import GooglePointFieldWidget

from apps.shared.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """
    Location model admin
    """
    list_display = (
        'address', 'coordinates',
    )
