# system
import os
import binascii
from decimal import Decimal

# django
from django.db import models


class Shop(models.Model):
    """
    Stores customer shops information
    """
    name = models.CharField(verbose_name='name', max_length=128)
    logo = models.ImageField(
        upload_to='logos',
        max_length=254,
        blank=True, null=True
    )
    api_key = models.CharField(
        verbose_name='API key',
        max_length=40,
        unique=True
    )
    allow_prepayment = models.BooleanField(
        verbose_name='Allow prepayment with MPesa from Payment Link form',
        default=False
    )
    default_delivery_fee = models.DecimalField(
        verbose_name='Default delivery fee',
        default=Decimal(0), decimal_places=2, max_digits=9
    )

    def __str__(self):
        return self.name

    def get_owners(self):
        from apps.core.models import UserRoles
        return self.users.filter(role=UserRoles.OWNER)

    def get_drivers(self):
        from apps.core.models import UserRoles
        return self.users.filter(role=UserRoles.DRIVER)

    def get_managers(self):
        from apps.core.models import UserRoles
        return self.users.filter(role=UserRoles.MANAGER)

    def get_orders(self):
        return self.orders.all()

    def get_pricelist_items(self):
        return self.pricelist_items.all()

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = self.generate_key()
        return super(Shop, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    @property
    def filled(self):
        return self.name and self.logo.name

    @property
    def get_logo(self):
        return self.logo.url if self.logo.name else \
            '/static/img/shop_default.svg'
