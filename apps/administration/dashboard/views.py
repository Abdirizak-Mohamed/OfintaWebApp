# django
from django.views.generic import TemplateView

from apps.core.models import OfintaUser, UserRoles


class DashboardView(TemplateView):
    template_name = 'administration/dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shop_accounts'] = OfintaUser.objects.filter(
            role=UserRoles.OWNER,
            is_active=True
        )
        context['admin_accounts'] = OfintaUser.objects.filter(
            role=UserRoles.ADMINISTRATOR,
            is_active=True
        ).exclude(pk=self.request.user.pk)
        return context
