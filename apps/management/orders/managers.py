# django
from django.db import models
from django.db.models.query_utils import Q

# ofinta
from apps.management.orders.constants import OrderStatus, PaymentMethod
from apps.mpesa_gateway.models import TransactionStatus


class OrderQuerySet(models.query.QuerySet):

    def get_pl(self):
        return self.filter(
            is_payment_link=True
        ).exclude(payment_link_id='')

    def get_paid(self):
        return self.filter(
            Q(
                Q(payment__transaction__status=TransactionStatus.SUCCESS) &
                Q(payment_method=PaymentMethod.MPESA)
            )
            | Q(payment_method=PaymentMethod.CASH)
            | Q(is_payment_link=True)
        )

    def get_open(self):
        return self.get_paid().exclude(
            status__in=[
                OrderStatus.CANCELED,
                OrderStatus.COMPLETED
            ]
        )

    def get_recent(self):
        return self.filter(
            status__in=[
                OrderStatus.CANCELED,
                OrderStatus.COMPLETED
            ]

        ).order_by('-completed_at')

    def get_new(self):
        return self.filter(status=OrderStatus.NEW)

    def get_submitted(self):
        return self.filter(status=OrderStatus.NEW)

    def get_accepted(self):
        return self.filter(status=OrderStatus.ACCEPTED)

    def get_assigned(self):
        return self.filter(status=OrderStatus.ASSIGNED)

    def get_picked_up(self):
        return self.filter(status=OrderStatus.PICKED_UP)

    def get_delivered(self):
        return self.filter(status=OrderStatus.DELIVERED)

    def get_completed(self):
        return self.filter(status=OrderStatus.COMPLETED)

    def get_canceled(self):
        return self.filter(status=OrderStatus.CANCELED)


class OrderManager(models.Manager):

    def get_pl(self):
        return self.get_queryset().filter(
            is_payment_link=True
        ).exclude(payment_link_id='')

    def get_paid(self):
        return self.get_queryset().filter(
            Q(
                Q(payment__transaction__status=TransactionStatus.SUCCESS) &
                Q(payment_method=PaymentMethod.MPESA)
            )
            | Q(payment_method=PaymentMethod.CASH)
            | Q(is_payment_link=True)
        )

    def get_open(self):
        return self.get_paid().get_open()

    def get_recent(self):
        return self.get_paid().get_recent()

    def get_new(self):
        return self.get_paid().get_new()

    def get_submitted(self):
        return self.get_paid().get_submitted()

    def get_accepted(self):
        return self.get_paid().get_accepted()

    def get_assigned(self):
        return self.get_paid().get_assigned()

    def get_picked_up(self):
        return self.get_paid().get_picked_up()

    def get_delivered(self):
        return self.get_paid().get_delivered()

    def get_completed(self):
        return self.get_paid().get_completed()

    def get_canceled(self):
        return self.get_paid().get_canceled()

    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)
