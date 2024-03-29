# django
from django import forms
from django.conf import settings
from django.forms import HiddenInput
from django.core.mail import send_mail
from django.template.loader import render_to_string

# ofinta
from apps.core.models import OfintaUser, UserRoles
from apps.management.shops.models import Shop


class ShopAccountAddForm(forms.ModelForm):
    shop_name = forms.CharField(required=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = UserRoles.OWNER
        self.fields['role'].widget = HiddenInput()

    class Meta:
        model = OfintaUser
        fields = ('first_name', 'last_name', 'email', 'role', 'shop_name')

    def save(self, commit=True):
        shop_account = super().save(commit)
        shop_name = self.cleaned_data['shop_name']
        shop = Shop.objects.create(name=shop_name)
        password = OfintaUser.objects.make_random_password()
        shop_account.set_password(password)
        shop_account.shop = shop
        shop_account.save()

        # ToDo: make email send - async (celery task)
        body_text = render_to_string(
            'administration/shop_accounts/email/'
            'shop_account_registration_body.txt',
            {'password': password}
        )
        send_mail(
            subject='Your shop account has been registered',
            message=body_text,
            from_email=settings.NOTIFICATIONS_EMAIL,
            recipient_list=[shop_account.email],
            fail_silently=True
        )


class ShopAccountEditForm(forms.ModelForm):

    class Meta:
        model = OfintaUser
        fields = ('first_name', 'last_name')


class ShopAccountBlockForm(forms.ModelForm):

    class Meta:
        model = OfintaUser
        fields = ()

    def save(self, commit=True):
        shop_account = super().save(commit)
        shop_account.is_active = False
        shop_account.save()
