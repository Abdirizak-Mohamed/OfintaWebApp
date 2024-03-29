# ofinta
from apps.core.models import OfintaUser, UserRoles


class AdminAccountsMixin:

    def get_queryset(self):
        return OfintaUser.objects.filter(
            role=UserRoles.ADMINISTRATOR
        ).exclude(
            pk=self.request.user.pk
        )

