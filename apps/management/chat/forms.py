# django
from django import forms

# ofinta
from apps.management.chat.models import Message


class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = ('message', )

    widgets = {
        'summary': forms.Textarea(attrs={'rows': 1, 'cols': 15}),
    }