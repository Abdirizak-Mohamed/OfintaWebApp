# django
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

# third party
from phonenumber_field.formfields import PhoneNumberField

# ofinta
from apps.core.models import OfintaUser, UserRoles
from apps.management.drivers.models import DriverProfile


class DriverForm(forms.ModelForm):

    phone = PhoneNumberField(required=False)
    driver_id = forms.CharField(max_length=64)
    bike_registration = forms.CharField(max_length=64)

    class Meta:
        model = OfintaUser
        fields = (
            'first_name', 'last_name', 'email',
            'phone', 'driver_id', 'bike_registration'
        )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=False):
        created = not self.instance.pk
        cd = self.cleaned_data
        phone = cd.pop('phone')
        driver_id = cd.pop('driver_id')
        bike_registration = cd.pop('bike_registration')
        driver = super().save()
        driver.shop = self.user.shop
        driver.role = UserRoles.DRIVER
        driver.save()

        if created:
            password = OfintaUser.objects.make_random_password(length=4,
                                                                allowed_chars='0123456789')
            driver.set_password(password)
            driver.save()

            # ToDo: make email send - async (celery task)
            body_text = render_to_string(
                'management/drivers/email/'
                'driver_registration_body.txt',
                {
                    'password': password, 'email': driver.email,
                    'first_name': driver.first_name,
                    'last_name': driver.last_name
                }
            )
            send_mail(
                subject='Your driver account at Ofinta has been registered',
                message=body_text,
                from_email=settings.NOTIFICATIONS_EMAIL,
                recipient_list=[driver.email]
            )

        profile, _ = DriverProfile.objects.get_or_create(
            user=driver,
            defaults={
                'phone': phone,
                'driver_id': driver_id,
                'bike_registration': bike_registration
            }
        )
        profile.phone = phone
        profile.driver_id = driver_id
        profile.bike_registration = bike_registration
        profile.save()
        return driver


class DriverStatusForm(forms.ModelForm):

    class Meta:
        model = OfintaUser
        fields = ()

    def save(self, commit=True):
        driver = super().save(commit)
        driver.is_active = not driver.is_active
        driver.save()
