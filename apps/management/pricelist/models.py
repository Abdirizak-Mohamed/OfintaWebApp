from decimal import Decimal

from django.db import models
from django.urls import reverse

from apps.management.shops.models import Shop


class PriceListItem(models.Model):
    """
    Stores price list item
    """
    shop = models.ForeignKey(
        Shop,
        verbose_name='shop',
        related_name='pricelist_items',
        on_delete=models.CASCADE
    )
    item_id = models.CharField(verbose_name='item id', max_length=255)
    name = models.CharField(verbose_name='item name', max_length=255)
    price = models.DecimalField(
        verbose_name='price',
        default=Decimal(0), decimal_places=2, max_digits=9
    )
    currency = models.CharField(
        verbose_name='currency', max_length=5, default='KES'
    )
    image = models.ImageField(
        upload_to='pricelist',
        max_length=254,
        blank=True, null=True
    )
    is_active = models.BooleanField(verbose_name='is active', default=True)

    def __str__(self):
        return f'Price list item: {self.name}. ' \
               f'Price: {self.price} {self.currency}'

    def get_absolute_url(self):
        return reverse('management:pricelist')

    @property
    def get_image(self):
        return self.image.url if self.image.name else None
