# django
from django.urls import path

# ofinta
from apps.management.shops.views import ShopSettings, ShopApiKeyRenew, ShopEdit

urlpatterns = [
    path('', ShopSettings.as_view(), name='settings'),
    path('edit/', ShopEdit.as_view(), name='edit-shop'),
    path('api-key-renew', ShopApiKeyRenew.as_view(), name='api-key-renew'),
]
