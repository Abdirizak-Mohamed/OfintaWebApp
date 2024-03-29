# third party
import pytest

# django
from django.urls import reverse

# ofinta
from rest_framework.authtoken.models import Token

from apps.core.models import UserRoles, OfintaUser
from apps.management.dashboard.tests.factories import ShopFactory, \
    DriverFactory, DriverProfileFactory


@pytest.mark.django_db
class TestDrivers:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self, manager):
        self.shop_1 = ShopFactory()

        self.manager = manager
        self.manager.shop = self.shop_1
        self.manager.save()

        self.driver_1_1 = DriverFactory(shop=self.shop_1)
        DriverProfileFactory(user=self.driver_1_1)
        self.driver_1_2 = DriverFactory(shop=self.shop_1)
        DriverProfileFactory(user=self.driver_1_2)
        self.driver_1_3 = DriverFactory(shop=self.shop_1, is_active=False)
        DriverProfileFactory(user=self.driver_1_3)

        # shop 2
        self.shop_2 = ShopFactory()

        self.driver_2_1 = DriverFactory(shop=self.shop_2)
        self.driver_2_2 = DriverFactory(shop=self.shop_2, is_active=False)

    def test_drivers_list(self, client):
        url = reverse('management:drivers-list')

        client.login(email=self.manager.email, password='password')

        response = client.get(url)
        assert response.status_code == 200
        context = response.context

        assert self.driver_1_1 in context['drivers']
        assert self.driver_1_2 in context['drivers']
        assert self.driver_1_3 in context['drivers']

        # drivers from the other shop not shown
        assert self.driver_2_1 not in context['drivers']
        assert self.driver_2_2 not in context['drivers']

    def test_driver_details(self, client):
        url = reverse(
            'management:driver-details', args=(self.driver_1_1.pk, )
        )

        client.login(email=self.manager.email, password='password')

        response = client.get(url)
        assert response.status_code == 200
        context = response.context

        assert self.driver_1_1 == context['driver']

        # manager has no access to the other shops drivers
        url = reverse(
            'management:driver-details', args=(self.driver_2_1.pk, )
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_driver_create(self, client):
        url = reverse('management:driver-add')

        client.login(email=self.manager.email, password='password')

        drivers_before = OfintaUser.objects.filter(
            role=UserRoles.DRIVER
        ).count()
        post_data = {
            'first_name': 'Ibrahim',
            'last_name': 'Azikiwe',
            'email': 'ibrahim.azikiwe@example.com',
            'phone': '+25420828732',
            'driver_id': '1234567890',
            'bike_registration': '1234567890'
        }
        response = client.post(url, post_data)
        drivers_after = OfintaUser.objects.filter(
            role=UserRoles.DRIVER
        ).count()
        assert response.url == reverse('management:drivers-list')
        assert response.status_code == 302

        new_driver = OfintaUser.objects.filter(role=UserRoles.DRIVER).last()
        assert new_driver.first_name == 'Ibrahim'
        assert new_driver.last_name == 'Azikiwe'
        assert new_driver.email == 'ibrahim.azikiwe@example.com'
        assert new_driver.role == UserRoles.DRIVER
        assert new_driver.shop == self.shop_1

        assert drivers_before + 1 == drivers_after

        # manager cannot create drivers for the shops where he is not manager
        drivers_before = OfintaUser.objects.filter(
            role=UserRoles.DRIVER
        ).count()
        post_data['shop'] = self.shop_2.pk
        response = client.post(url, post_data)
        drivers_after = OfintaUser.objects.filter(
            role=UserRoles.DRIVER
        ).count()
        assert response.context['form'].is_valid() is False
        assert response.status_code == 200
        assert drivers_before == drivers_after

    def test_driver_edit(self, client):
        url = reverse(
            'management:driver-edit', args=(self.driver_1_1.pk, )
        )

        client.login(email=self.manager.email, password='password')

        post_data = {
            'first_name': 'Ibrahim 2',
            'last_name': 'Azikiwe',
            'email': 'ibrahim.azikiwe@example.com',
            'phone': '+25420828732',
            'driver_id': '1234567890',
            'bike_registration': '1234567890'
        }
        response = client.post(url, post_data)
        assert response.status_code == 302
        assert response.url == reverse(
            'management:driver-details', args=(self.driver_1_1.pk, )
        )
        self.driver_1_1.refresh_from_db()
        assert self.driver_1_1.first_name == 'Ibrahim 2'

        # manager cannot move drivers to the shops where he is not manager
        url = reverse(
            'management:driver-edit', args=(self.driver_2_1.pk, )
        )
        post_data['first_name'] = 'Ibrahim (new)'
        post_data['shop'] = self.shop_2.pk
        response = client.post(url, post_data)
        assert response.status_code == 404

    def test_driver_status(self, client):
        url = reverse(
            'management:driver-status', args=(self.driver_1_1.pk, )
        )

        client.login(email=self.manager.email, password='password')

        response = client.post(url, {})
        assert response.status_code == 302
        assert response.url == reverse(
            'management:driver-details', args=(self.driver_1_1.pk, )
        )
        self.driver_1_1.refresh_from_db()
        assert self.driver_1_1.is_active == False

        response = client.post(url, {})
        assert response.status_code == 302
        self.driver_1_1.refresh_from_db()
        assert self.driver_1_1.is_active == True

        # manager cannot change driver status from the shops
        # where he is not manager
        url = reverse(
            'management:driver-edit', args=(self.driver_2_1.pk, )
        )
        response = client.post(url, {})
        assert response.status_code == 404

    def test_driver_login(self, client):
        url = reverse('management:driver-login')

        response = client.post(
            url,
            {'username': self.driver_1_1.email, 'password': 'password'}
        )
        token = Token.objects.get(user=self.driver_1_1)
        assert response.json() == {
            'token': token.key,
            'user': self.driver_1_1.id
        }

        # try to get token as manager
        response = client.post(
            url,
            {'username': self.manager.email, 'password': 'password'}
        )
        assert response.json() == {
            'non_field_errors': ['Only drivers can obtain API token']
        }
