# django
from django.urls import path, include


urlpatterns = [
    path(
        '',
        include('apps.management.dashboard.urls'),
    ),
    path(
        'orders/',
        include('apps.management.orders.urls'),
    ),
    path(
        'drivers/',
        include('apps.management.drivers.urls'),
    ),
    path(
        'reports/',
        include('apps.management.reports.urls'),
    ),
    path(
        'chat/',
        include('apps.management.chat.urls'),
    ),
    path(
        'settings/',
        include('apps.management.shops.urls'),
    ),
    path(
        'warehouses/',
        include('apps.management.warehouses.urls'),
    ),
    path(
        'managers/',
        include('apps.management.managers.urls'),
    ),
    path(
        'pricelist/',
        include('apps.management.pricelist.urls'),
    )
]
