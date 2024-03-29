# system
import logging

# django
from django import forms

# third party
from django_select2.forms import Select2Widget
from django_file_form.fields import UploadedFileField
from django_file_form.forms import FileFormMixin
from django_filters.fields import ModelMultipleChoiceField

# ofinta
from apps.management.pricelist.models import PriceListItem


logger = logging.getLogger(__name__)


class PriceListSearchForm(forms.Form):

    class Meta:
        fields = ('items', 'query')

    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)
        if user:
            shop = user.shop
            self.fields['items'].queryset = PriceListItem.objects.filter(
                shop=shop
            )

        self.fields['items'].widget.attrs['placeholder'] = 'Search by ID or name'
        self.fields['query'].widget.attrs['placeholder'] = 'Filter by ID or name'

    items = ModelMultipleChoiceField(
        queryset=PriceListItem.objects.all(),
        widget=Select2Widget
    )
    query = forms.CharField()


class PriceListItemForm(FileFormMixin, forms.ModelForm):

    image = UploadedFileField(required=False)

    class Meta:
        model = PriceListItem
        fields = ('item_id', 'name', 'price', 'image')
