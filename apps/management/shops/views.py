# django
from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, UpdateView

# ofinta
from apps.management.shops.forms import ShopApiKeyRenewForm, ShopEditForm
from apps.management.shops.models import Shop

from apps.management.mixins import AdminTestMixin, OwnerTestMixin


class ShopSettings(OwnerTestMixin, DetailView):
    model = Shop
    context_object_name = 'shop'
    template_name = 'management/shops/shop_settings.html'

    def get_object(self, queryset=None):
        return self.request.user.shop


class ShopEdit(OwnerTestMixin, UpdateView):
    model = Shop
    form_class = ShopEditForm
    context_object_name = 'shop'
    template_name = 'management/shops/shop_edit.html'

    def get_object(self, queryset=None):
        return self.request.user.shop

    def get_success_url(self):
        return reverse('management:settings')


class ShopApiKeyRenew(AdminTestMixin, UpdateView):
    model = Shop
    form_class = ShopApiKeyRenewForm
    context_object_name = 'shop'
    template_name = 'management/shops/shop_settings.html'
    success_url = reverse_lazy('management:settings')

    def get_object(self, queryset=None):
        return self.request.user.shop

    def get_success_url(self):
        return reverse('management:settings')
