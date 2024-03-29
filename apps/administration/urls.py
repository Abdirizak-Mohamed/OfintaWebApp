# django
from django.urls import path, include


urlpatterns = [
    path(
        '',
        include(
            'apps.administration.dashboard.urls',
        ),
    ),
    path(
        'shop_accounts/',
        include('apps.administration.shop_accounts.urls'),
    ),
    path(
        'administrators/',
        include('apps.administration.admin_accounts.urls'),
    ),
]
