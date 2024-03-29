# django
from django import forms

# ofinta
from django.forms import HiddenInput

# ofinta
from django.contrib.gis.geos import Point
from apps.core.utils import get_coordinates_by_address
from apps.management.shops.models import Shop
from apps.management.warehouses.models import Warehouse
from apps.shared.models import Location


class WarehouseCreateForm(forms.ModelForm):

    address = forms.CharField(required=True, max_length=255)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shop = user.shop
        self.fields['shop'].queryset = Shop.objects.filter(id=user.shop.id)
        self.fields['shop'].initial = shop
        self.fields['shop'].widget = HiddenInput()

    class Meta:
        model = Warehouse
        fields = ('name', 'code', 'shop', 'address')

    def save(self, commit=True):
        warehouse = super().save(commit=False)
        address = self.cleaned_data['address']
        location = Location.objects.create(address=address)
        lat, lng = get_coordinates_by_address(address)
        location.coordinates = Point(lat, lng)
        warehouse.address = address
        warehouse.location = location
        warehouse.save()
        return warehouse


class WarehouseEditForm(forms.ModelForm):

    address = forms.CharField(required=True, max_length=255)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].initial = self.instance.location.address
        shop = user.shop
        self.fields['shop'].queryset = Shop.objects.filter(id=user.shop.id)
        self.fields['shop'].initial = shop
        self.fields['shop'].widget = HiddenInput()

    class Meta:
        model = Warehouse
        fields = ('name', 'code', 'shop', 'address')

    def save(self, commit=True):
        warehouse = super().save(commit=False)
        address = self.cleaned_data['address']
        lat, lng = get_coordinates_by_address(address)
        warehouse.location.address = address
        warehouse.location.coordinates = Point(lat, lng)
        warehouse.location.save()
        warehouse.save()
