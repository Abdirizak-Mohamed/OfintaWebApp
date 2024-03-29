# ofinta
from apps.core.models import UserRoles


class ManagersMixin:

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_managers().filter(
            role=UserRoles.MANAGER
        )

