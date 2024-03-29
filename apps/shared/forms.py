# django
from django import forms

# ofinta
from apps.shared.models import Location
from apps.shared.widgets import CustomGooglePointFieldWidget


class LocationForm(forms.ModelForm):

    class Meta:
        model = Location
        fields = ('coordinates', )
        widgets = {
            'coordinates': CustomGooglePointFieldWidget
        }
