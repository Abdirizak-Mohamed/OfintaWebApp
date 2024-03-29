# system
import datetime

# django
from django.conf import settings
from django.utils import timezone
from django.db import models


class DriverQueryset(models.query.QuerySet):

    def get_active(self):
        last_update_datetime = timezone.now() - datetime.timedelta(
            seconds=settings.DRIVER_UPDATE_TIMEOUT
        )
        return self.filter(
            last_update__gte=last_update_datetime
        )


class DriverManager(models.Manager):

    def get_active(self):
        last_update_datetime = timezone.now() - datetime.timedelta(
            seconds=settings.DRIVER_UPDATE_TIMEOUT
        )
        return self.get_queryset().filter(
            last_update__gte=last_update_datetime
        )

    def get_queryset(self):
        return DriverQueryset(self.model, using=self._db)
