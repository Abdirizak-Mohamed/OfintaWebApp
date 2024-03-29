# django
from django.conf import settings
from django.apps import AppConfig
from django.db.models.signals import post_delete

# ofinta
from apps.administration.shop_accounts.signals import shop_account_removed


class ShopAccountsConfig(AppConfig):
    name = 'apps.administration.shop_accounts'

    def ready(self):
        post_delete.connect(
            shop_account_removed,
            sender=settings.AUTH_USER_MODEL,
            dispatch_uid='shop_account_removed'
        )
