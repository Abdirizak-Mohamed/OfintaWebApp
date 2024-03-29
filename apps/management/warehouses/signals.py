# ofinta
from django.db.models.aggregates import Max

from apps.management.orders.models import Order


def generate_code(sender, instance=None, **kwargs):
    """
    Generate warehouse code on create
    """
    if not instance.code:
        instance.code = f'wh-{instance.shop.id}-{instance.id}'


def generate_order_number(sender, instance=None, **kwargs):
    """
    Generate warehouse code on create
    """
    max_order_number = Order.objects.all().aggregate(
        Max('order_number')
    )['order_number__max']
    if not instance.order_number:
        instance.order_number = max_order_number + 1
