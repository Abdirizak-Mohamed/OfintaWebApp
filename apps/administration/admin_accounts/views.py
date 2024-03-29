# django
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView, CreateView, \
    DeleteView

# ofinta
from apps.administration.admin_accounts.forms import AdminAccountAddForm, \
    AdminAccountBlockForm, AdminAccountEditForm
from apps.administration.admin_accounts.mixins import AdminAccountsMixin
from apps.core.models import OfintaUser


class AdminAccountsList(LoginRequiredMixin, AdminAccountsMixin, ListView):
    model = OfintaUser
    template_name = 'administration/admin_accounts/admin_accounts_list.html'
    context_object_name = 'admin_accounts'


class AdminAccountDetails(LoginRequiredMixin, AdminAccountsMixin, DetailView):
    model = OfintaUser
    template_name = 'administration/admin_accounts/admin_account_details.html'
    context_object_name = 'admin_account'

    def get_context_data(self, **kwargs):
        shop_account = self.get_object()
        context = super().get_context_data()
        context['form'] = AdminAccountBlockForm(instance=shop_account)
        return context


class AdminAccountAdd(LoginRequiredMixin, CreateView):
    model = OfintaUser
    form_class = AdminAccountAddForm
    template_name = 'administration/admin_accounts/admin_account_add.html'

    def get_success_url(self):
        return reverse('administration:admin-accounts-list')


class AdminAccountEdit(LoginRequiredMixin, AdminAccountsMixin, UpdateView):
    model = OfintaUser
    form_class = AdminAccountEditForm
    template_name = 'administration/admin_accounts/admin_account_edit.html'
    context_object_name = 'admin_account'

    def get_success_url(self):
        admin_account = self.get_object()
        return reverse(
            'administration:admin-account-details', args=(admin_account.pk, )
        )


class AdminAccountBlock(LoginRequiredMixin, AdminAccountsMixin, UpdateView):
    model = OfintaUser
    form_class = AdminAccountBlockForm
    template_name = 'administration/admin_accounts/admin_account_edit.html'
    context_object_name = 'admin_account'

    def get_success_url(self):
        return reverse('administration:admin-accounts-list')


class AdminAccountRemove(LoginRequiredMixin, AdminAccountsMixin, DeleteView):
    model = OfintaUser
    template_name = 'administration/admin_accounts/admin_account_remove.html'
    context_object_name = 'admin_account'

    def get_success_url(self):
        return reverse('administration:admin-accounts-list')
