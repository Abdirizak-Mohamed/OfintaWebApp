# django
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# ofinta
from apps.core.models import UserRoles
from apps.management.drivers.models import DriverProfile


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'management/dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        shop = user.shop
        if not shop:
            return context

        context['active_orders'] = shop.get_orders().get_open()[
            :settings.MAX_ORDERS_ON_DASH
        ]
        context['recent_orders'] = shop.get_orders().get_recent()[
            :settings.MAX_ORDERS_ON_DASH
        ]

        drivers = shop.get_drivers()
        drivers_profiles = DriverProfile.objects.filter(
            user__in=drivers
        )
        active_drivers = drivers_profiles.get_active()
        active_drivers = drivers.filter(driver_profile__in=active_drivers)
        context['active_drivers'] = active_drivers

        inactive_drivers = drivers_profiles.exclude(
            user__id__in=active_drivers.values_list('id')
        )
        inactive_drivers = drivers.filter(driver_profile__in=inactive_drivers)
        context['inactive_drivers'] = inactive_drivers

        context['warehouses'] = shop.warehouses.all(
        )[:settings.MAX_WAREHOUSES_ON_DASH]

        if user.is_owner:
            context['managers'] = shop.get_managers().filter(
                role=UserRoles.MANAGER
            )
        return context
