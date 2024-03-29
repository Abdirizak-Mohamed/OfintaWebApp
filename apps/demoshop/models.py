from django.db import models


class DemoProduct(models.Model):
    price = models.DecimalField(
        verbose_name='price',
        decimal_places=2, max_digits=9
    )
    name = models.CharField(verbose_name='name', max_length=255)

    def __str__(self):
        return self.name
