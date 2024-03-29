# django
from django.db import models


class OrderQuerySet(models.query.QuerySet):


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
