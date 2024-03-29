# django
from django.db import models

# ofinta
from django.urls import reverse

from apps.management.shops.models import Shop
from apps.shared.models import Location


class Warehouse(models.Model):
    """
    Stores customer's shop warehouse information
    """
    code = models.CharField(verbose_name='code', max_length=20)
    shop = models.ForeignKey(
        Shop,
        verbose_name='shop',
        on_delete=models.CASCADE,
        related_name='warehouses'
    )
    name = models.CharField(verbose_name='name', max_length=128)
    location = models.ForeignKey(
        Location,
        verbose_name='location',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'Warehouse "{self.name}"'

    def get_absolute_url(self):
        return reverse('management:warehouse-details', args=(self.pk, ))
