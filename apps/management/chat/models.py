# django
from django.db import models

# ofinta
from apps.core.models import OfintaUser
from apps.management.shops.models import Shop


class Message(models.Model):
    sender = models.ForeignKey(
        OfintaUser,
        on_delete=models.CASCADE,
        verbose_name='sender',
        related_name='sent_messages'
    )
    message = models.TextField(verbose_name='message', max_length=4000)
    timestamp = models.DateTimeField(
        verbose_name='timestamp',
        auto_now_add=True
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name='shop',
        related_name='messages',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.message

    class Meta:
        ordering = ('timestamp',)
