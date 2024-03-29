# ofinta
from django.core.exceptions import PermissionDenied

from apps.core.models import UserRoles


class OwnerRequiredMixin:

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.role not in \
               [UserRoles.OWNER, UserRoles.ADMINISTRATOR]:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
