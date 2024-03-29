# system
import logging

# django
from django.contrib.gis.db.models import PointField
from django.db import models
from django.urls import reverse

# third party
from phonenumber_field.modelfields import PhoneNumberField

# ofinta
from push_notifications.models import GCMDevice
from apps.core.models import OfintaUser
from apps.management.drivers.managers import DriverManager


logger = logging.getLogger(__name__)


class DriverProfile(models.Model):
    """
    Stores driver information

    """
    user = models.OneToOneField(
        OfintaUser,
        verbose_name='user',
        related_name='driver_profile',
        on_delete=models.CASCADE
    )
    phone = PhoneNumberField(verbose_name='phone')
    driver_id = models.CharField(verbose_name='driver id', max_length=64)
    bike_registration = models.CharField(
        verbose_name='bike registration',
        max_length=64
    )
    coordinates = PointField(
        verbose_name='coordinates',
        null=True, blank=True
    )
    last_update = models.DateTimeField(
        verbose_name='last update',
        auto_now=True
    )
    photo = models.ImageField(
        upload_to='photos',
        max_length=254,
        blank=True, null=True
    )

    objects = DriverManager()

    def __str__(self):
        return f'Driver: {self.user.first_name} {self.user.last_name} ' \
               f'({self.driver_id})'

    def get_absolute_url(self):
        return reverse('management:driver-details', args=(self.pk, ))

    @property
    def get_photo(self):
        return self.photo.url if self.photo.name else \
            '/static/img/user_default.svg'

    def send_push(self, message, push_extra, order=None):
        from apps.api.v1.serializers import OrderSerializer
        driver_device = GCMDevice.objects.filter(
            cloud_message_type='FCM',
            user=self.user,
            active=True
        ).last()

        if order:
            serializer = OrderSerializer(order)
            push_extra.update(**{'order': serializer.data})

        if driver_device:
            driver_device.send_message(message, extra=push_extra)
        else:
            logger.warning(
                'Current driver {} has no registered and active device'.format(
                    self.user.email
                )
            )