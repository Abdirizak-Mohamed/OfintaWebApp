# django
from django import forms

from apps.management.shops.models import Shop


class ShopApiKeyRenewForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ()

    def save(self, commit=True):
        self.instance.api_key = self.instance.generate_key()
        self.instance.save()


class ShopEditForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ('name', 'logo', 'allow_prepayment', 'default_delivery_fee')
