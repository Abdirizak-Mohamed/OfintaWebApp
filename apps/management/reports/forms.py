# django
from django import forms


class ReportsFilterForm(forms.Form):

    start_date = forms.DateField(label='Date range start', required=False)
    end_date = forms.DateField(label='Date range end', required=False)

    class Meta:
        fields = (
            'start_date', 'end_date'
        )
