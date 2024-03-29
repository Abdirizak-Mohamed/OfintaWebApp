# django
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView, CreateView, \
    DeleteView

# ofinta
from apps.administration.shop_accounts.forms import ShopAccountBlockForm, \
    ShopAccountAddForm, ShopAccountEditForm
from apps.administration.shop_accounts.mixins import ShopAccountsMixin
from apps.core.models import OfintaUser


class ShopAccountsList(LoginRequiredMixin, ShopAccountsMixin, ListView):
    model = OfintaUser
    template_name = 'administration/shop_accounts/shop_accounts_list.html'
    context_object_name = 'shop_accounts'


class ShopAccountDetails(LoginRequiredMixin, ShopAccountsMixin, DetailView):
    model = OfintaUser
    template_name = 'administration/shop_accounts/shop_account_details.html'
    context_object_name = 'shop_account'

    def get_context_data(self, **kwargs):
        shop_account = self.get_object()
        context = super().get_context_data()
        context['form'] = ShopAccountBlockForm(instance=shop_account)
        return context


class ShopAccountAdd(LoginRequiredMixin, CreateView):
    model = OfintaUser
    form_class = ShopAccountAddForm
    template_name = 'administration/shop_accounts/shop_account_add.html'

    def get_success_url(self):
        return reverse('administration:shop-accounts-list')


class ShopAccountEdit(LoginRequiredMixin, ShopAccountsMixin, UpdateView):
    model = OfintaUser
    form_class = ShopAccountEditForm
    template_name = 'administration/shop_accounts/shop_account_edit.html'
    context_object_name = 'shop_account'

    def get_success_url(self):
        shop_account = self.get_object()
        return reverse(
            'administration:shop-account-details', args=(shop_account.pk, )
        )


class ShopAccountBlock(LoginRequiredMixin, ShopAccountsMixin, UpdateView):
    model = OfintaUser
    form_class = ShopAccountBlockForm
    template_name = 'administration/shop_accounts/shop_account_edit.html'
    context_object_name = 'shop_account'

    def get_success_url(self):
        return reverse('administration:shop-accounts-list')


class ShopAccountRemove(LoginRequiredMixin, ShopAccountsMixin, DeleteView):
    model = OfintaUser
    template_name = 'administration/shop_accounts/shop_account_remove.html'
    context_object_name = 'shop_account'

    def get_success_url(self):
        return reverse('administration:shop-accounts-list')

