# ofinta
from apps.core.models import OfintaUser, UserRoles


class ShopAccountsMixin:

    def get_queryset(self):
        return OfintaUser.objects.filter(role=UserRoles.OWNER)

