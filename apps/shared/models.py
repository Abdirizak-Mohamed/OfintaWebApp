# third party
from django.contrib.gis.db import models


class Location(models.Model):
    """
    Stores any location described by address and geolocation point
    """
    address = models.CharField(
        verbose_name='address',
        max_length=255,
        blank=True
    )
    coordinates = models.PointField(
        verbose_name='coordinates',
        null=True, blank=True
    )

    def __str__(self):
        return self.address
