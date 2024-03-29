# django
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView, CreateView

# ofinta
from apps.management.drivers.forms import DriverStatusForm, DriverForm
from apps.management.drivers.mixins import DriversMixin
from apps.management.drivers.models import OfintaUser, DriverProfile


class DriversList(LoginRequiredMixin, DriversMixin, ListView):
    model = OfintaUser
    template_name = 'management/drivers/drivers_list.html'
    context_object_name = 'drivers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        drivers = context['drivers']
        drivers_profiles = DriverProfile.objects.filter(
            user__in=drivers
        )
        active_drivers = drivers_profiles.get_active()
        active_drivers = drivers.filter(driver_profile__in=active_drivers)
        inactive_drivers = drivers_profiles.exclude(
            user__id__in=active_drivers.values_list('id')
        )
        inactive_drivers = drivers.filter(driver_profile__in=inactive_drivers)
        context['active_drivers'] = active_drivers
        context['inactive_drivers'] = inactive_drivers

        drivers_coords = []
        for active_driver in active_drivers:

            if not active_driver.driver_profile.coordinates:
                continue

            latitude = active_driver.driver_profile.coordinates.x
            longitude = active_driver.driver_profile.coordinates.y

            drivers_coords.append([latitude, longitude])

        context['drivers_coords'] = drivers_coords
        return context


class DriverDetails(LoginRequiredMixin, DriversMixin, DetailView):
    model = OfintaUser
    template_name = 'management/drivers/driver_details.html'
    context_object_name = 'driver'

    def get_context_data(self, **kwargs):
        driver = self.get_object()
        context = super().get_context_data()
        context['form'] = DriverStatusForm(instance=driver)
        return context


class DriverAdd(LoginRequiredMixin, CreateView):
    model = OfintaUser
    form_class = DriverForm
    template_name = 'management/drivers/driver_add.html'

    def get_success_url(self):
        return reverse('management:drivers-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class DriverEdit(LoginRequiredMixin, DriversMixin, UpdateView):
    model = OfintaUser
    form_class = DriverForm
    template_name = 'management/drivers/driver_edit.html'
    context_object_name = 'driver'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        driver = self.get_object()
        return reverse('management:driver-details', args=(driver.pk, ))


class DriverStatus(LoginRequiredMixin, DriversMixin, UpdateView):
    model = OfintaUser
    form_class = DriverStatusForm
    template_name = 'management/drivers/driver_edit.html'
    context_object_name = 'driver'

    def get_success_url(self):
        driver = self.get_object()
        return reverse('management:driver-details', args=(driver.pk, ))
