# django
from django import forms
from django.conf import settings
from django.forms import HiddenInput
from django.core.mail import send_mail
from django.template.loader import render_to_string

# ofinta
from apps.core.models import OfintaUser, UserRoles


class AdminAccountAddForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = UserRoles.ADMINISTRATOR
        self.fields['role'].widget = HiddenInput()

    class Meta:
        model = OfintaUser
        fields = ('first_name', 'last_name', 'email', 'role')

    def save(self, commit=True):
        admin_account = super().save(commit)
        password = OfintaUser.objects.make_random_password()
        admin_account.set_password(password)
        admin_account.save()

        # ToDo: make email send - async (celery task)
        body_text = render_to_string(
            'administration/admin_accounts/email/'
            'admin_account_registration_body.txt',
            {'password': password}
        )
        send_mail(
            subject='Your administrator account has been account registered',
            message=body_text,
            from_email=settings.NOTIFICATIONS_EMAIL,
            recipient_list=[admin_account.email]
        )


class AdminAccountEditForm(forms.ModelForm):

    class Meta:
        model = OfintaUser
        fields = ('first_name', 'last_name')


class AdminAccountBlockForm(forms.ModelForm):

    class Meta:
        model = OfintaUser
        fields = ()

    def save(self, commit=True):
        admin_account = super().save(commit)
        admin_account.is_active = False
        admin_account.save()
