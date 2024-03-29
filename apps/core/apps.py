# django
from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    name = 'apps.core'

    def ready(self):
        from apps.core.signals import create_auth_token
        from django.db.models.signals import post_save
        post_save.connect(
            create_auth_token,
            sender=settings.AUTH_USER_MODEL,
            dispatch_uid='user_created'
        )
