# django
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.forms import HiddenInput
from django.template.loader import render_to_string

# ofinta
from apps.core.models import OfintaUser, UserRoles
from apps.management.shops.models import Shop


class ManagerForm(forms.ModelForm):

    class Meta:
        model = OfintaUser
        fields = ('first_name', 'last_name', 'email', 'role', 'shop')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shop = user.shop
        self.fields['shop'].queryset = Shop.objects.filter(
            id__in=[shop.id]
        )
        self.fields['shop'].initial = shop
        self.fields['shop'].widget = HiddenInput()
        self.fields['role'].initial = UserRoles.MANAGER
        self.fields['role'].widget = HiddenInput()

    def save(self, commit=True):
        created = not self.instance.pk
        manager_account = super().save(commit)

        if created:
            password = OfintaUser.objects.make_random_password()
            manager_account.set_password(password)
            manager_account.save()

            # ToDo: make email send - async (celery task)
            body_text = render_to_string(
                'administration/admin_accounts/email/'
                'admin_account_registration_body.txt',
                {'password': password}
            )
            send_mail(
                subject='Your manager account has been account registered',
                message=body_text,
                from_email=settings.NOTIFICATIONS_EMAIL,
                recipient_list=[manager_account.email]
            )


class ManagerStatusForm(forms.ModelForm):

    class Meta:
        model = OfintaUser
        fields = ()

    def save(self, commit=True):
        manager = super().save(commit)
        manager.is_active = not manager.is_active
        manager.save()
