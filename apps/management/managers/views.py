# django
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView, CreateView, \
    DeleteView

# ofinta
from apps.core.models import OfintaUser
from apps.management.dashboard.mixins import OwnerRequiredMixin
from apps.management.managers.forms import ManagerStatusForm, ManagerForm
from apps.management.managers.mixins import ManagersMixin


class ManagersList(LoginRequiredMixin, OwnerRequiredMixin,
                   ManagersMixin, ListView):
    model = OfintaUser
    template_name = 'management/managers/managers_list.html'
    context_object_name = 'managers'


class ManagerDetails(LoginRequiredMixin, OwnerRequiredMixin,
                     ManagersMixin, DetailView):
    model = OfintaUser
    template_name = 'management/managers/manager_details.html'
    context_object_name = 'manager'

    def get_context_data(self, **kwargs):
        manager = self.get_object()
        context = super().get_context_data()
        context['form'] = ManagerStatusForm(instance=manager)
        return context


class ManagerAdd(LoginRequiredMixin, OwnerRequiredMixin, CreateView):
    model = OfintaUser
    form_class = ManagerForm
    template_name = 'management/managers/manager_add.html'

    def get_success_url(self):
        return reverse('management:managers-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class ManagerEdit(LoginRequiredMixin, OwnerRequiredMixin,
                  ManagersMixin, UpdateView):
    model = OfintaUser
    form_class = ManagerForm
    template_name = 'management/managers/manager_edit.html'
    context_object_name = 'manager'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        manager = self.get_object()
        return reverse('management:manager-details', args=(manager.pk, ))


class ManagerStatus(LoginRequiredMixin, OwnerRequiredMixin,
                          ManagersMixin, UpdateView):
    model = OfintaUser
    form_class = ManagerStatusForm
    template_name = 'management/managers/manager_edit.html'
    context_object_name = 'manager'

    def get_success_url(self):
        manager = self.get_object()
        return reverse('management:manager-details', args=(manager.pk, ))


class ManagerRemove(LoginRequiredMixin, OwnerRequiredMixin,
                    ManagersMixin, DeleteView):
    model = OfintaUser
    template_name = 'management/managers/manager_remove.html'
    context_object_name = 'manager'

    def get_success_url(self):
        return reverse('management:managers-list')
