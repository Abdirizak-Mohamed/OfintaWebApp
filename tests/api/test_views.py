# system
import json

# third party
import pytest
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.reverse import reverse

# ofinta
from apps.core.models import OfintaUser
from apps.management.chat.models import Message
from apps.management.dashboard.tests.factories import DriverProfileFactory, \
    OrderFactory, ShopFactory, TransactionFactory
from apps.management.orders.constants import OrderStatus, OrderAssignmentStatus, \
    PaymentMethod, PaymentStatus
from apps.management.orders.models import OrderAssignments, Payment, Order
from apps.mpesa_gateway.models import TransactionStatus


class TestDriversEndpoint:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.shop_1 = ShopFactory()

        self.driver_profile = DriverProfileFactory()
        self.driver_profile.phone = '254702595945'
        self.driver_profile.coordinates = Point(39.6650254, -4.060741999999999)
        self.driver_profile.save()

        self.driver = self.driver_profile.user
        self.driver.shop = self.shop_1
        self.driver.save()

        # active orders
        self.active_order_1_1 = OrderFactory(
            shop=self.shop_1,
            order_number=1,
            verification_code='confcode'
        )
        self.payment_1_1 = Payment.objects.create(order=self.active_order_1_1)
        self.payment_1_1.transaction = TransactionFactory(
            status=TransactionStatus.SUCCESS
        )
        self.payment_1_1.save()

        self.active_order_1_1.driver = None
        self.active_order_1_1.save()

        self.active_order_1_2 = OrderFactory(
            shop=self.shop_1,
            order_number=2,
            status=OrderStatus.ASSIGNED
        )
        self.payment_1_2 = Payment.objects.create(order=self.active_order_1_2)
        self.payment_1_2.transaction = TransactionFactory(
            status=TransactionStatus.SUCCESS
        )
        self.payment_1_2.save()

        self.active_order_1_3 = OrderFactory(
            shop=self.shop_1,
            order_number=3,
            status=OrderStatus.ASSIGNED
        )
        self.payment_1_3 = Payment.objects.create(order=self.active_order_1_3)
        self.payment_1_3.transaction = TransactionFactory(
            status=TransactionStatus.SUCCESS
        )
        self.payment_1_3.save()

        self.active_order_1_2.warehouse.location.coordinates = Point(
            39.6650254, -4.060741999999999
        )
        self.active_order_1_2.warehouse.location.save()

        # recent orders
        self.inactive_order_1_1 = OrderFactory(
            shop=self.shop_1,
            order_number=4,
            status=OrderStatus.CANCELED
        )
        self.inactive_order_1_2 = OrderFactory(
            shop=self.shop_1,
            order_number=5,
            status=OrderStatus.COMPLETED
        )

        # shop 2
        self.shop_2 = ShopFactory()

        # active orders (shop 2)
        self.active_order_2_1 = OrderFactory(
            shop=self.shop_2,
            order_number=6,
            status=OrderStatus.ASSIGNED
        )

        # recent orders (shop 2)
        self.active_order_2_2 = OrderFactory(
            shop=self.shop_2,
            order_number=7,
            status=OrderStatus.COMPLETED
        )

    def test_profile_get(self, client):
        """
        Test GET request to /api/v1/driver/profile/
        """
        url = reverse('api:v1:driver-profile')

        # send request without token
        response = client.get(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        response = client.get(url, **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'user': {
                'email': self.driver.email,
                'first_name': self.driver.first_name,
                'last_name': self.driver.last_name
            },
            'phone': str(self.driver_profile.phone),
            'driver_id': self.driver_profile.driver_id,
            'bike_registration': self.driver_profile.bike_registration,
            'coordinates': {
                'type': 'Point', 'coordinates': [39.6650254, -4.060742]
            },
            'last_update': self.driver_profile.last_update.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
            'photo': None
        }

        # set User.changed_password to False
        driver = OfintaUser.objects.get(id=self.driver.id)
        driver.changed_password = False
        driver.save()

        self.driver.refresh_from_db()

        response = client.get(url, **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'user': {
                'email': self.driver.email,
                'first_name': self.driver.first_name,
                'last_name': self.driver.last_name
            },
            'phone': str(self.driver_profile.phone),
            'driver_id': self.driver_profile.driver_id,
            'bike_registration': self.driver_profile.bike_registration,
            'coordinates': {
                'type': 'Point', 'coordinates': [39.6650254, -4.060742]
            },
            'last_update': self.driver_profile.last_update.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
            'photo': None,
            'changed_password': self.driver.changed_password
        }

    def test_profile_patch(self, client):
        """
        Test PATCH request to /api/v1/driver/profile/
        """
        url = reverse('api:v1:driver-profile')

        # send request without token
        response = client.get(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        patch_data = {'phone': '+254702595910'}
        response = client.patch(url, json.dumps(patch_data), **headers)
        self.driver_profile.refresh_from_db()
        assert str(self.driver_profile.phone) == '+254702595910'
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'user': {
                'email': self.driver.email,
                'first_name': self.driver.first_name,
                'last_name': self.driver.last_name
            },
            'phone': str(self.driver_profile.phone),
            'driver_id': self.driver_profile.driver_id,
            'bike_registration': self.driver_profile.bike_registration,
            'coordinates': {
                'type': 'Point', 'coordinates': [39.6650254, -4.060742]
            },
            'last_update': self.driver_profile.last_update.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
            'photo': None
        }

    def test_location_set(self, client):
        """
        Test PATCH request to /api/v1/driver/location/
        """
        url = reverse('api:v1:driver-location')

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        latitude = 39.6650254
        longitude = -4.060741999999999
        patch_data = {
            'latitude': latitude,
            'longitude': longitude
        }
        response = client.patch(url, data=json.dumps(patch_data), **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'latitude': latitude, 'longitude': longitude
        }

        self.driver_profile.refresh_from_db()
        assert self.driver_profile.coordinates.x == latitude
        assert self.driver_profile.coordinates.y == longitude

    def test_skip(self, client):
        """
        Test PATCH request to /api/v1/driver/orders/<pk>/skip/
        """
        url = reverse('api:v1:skip-order', args=(self.active_order_1_1.pk, ))

        # send request without token
        response = client.post(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }

        # try to skip order with status != "assigned"
        assignment = OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_1
        )
        response = client.post(url, data=json.dumps({}), **headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'message': 'Current order cannot be skipped at the moment'
        }
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.NEW

        # change order status to `assigned`
        self.active_order_1_1.status = OrderStatus.ASSIGNED
        self.active_order_1_1.save()
        response = client.post(url, data=json.dumps({}), **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'message': 'Order skipped'}

        self.active_order_1_1.refresh_from_db()
        assignment.refresh_from_db()
        assert assignment.status == OrderAssignmentStatus.REJECTED
        assert self.active_order_1_1.status == OrderStatus.NEW
        assert self.active_order_1_1.driver is None

        # try to change order status for the shop he is not member of
        url = reverse('api:v1:skip-order', args=(self.active_order_2_1.pk,))
        response = client.post(url, data=json.dumps({}), **headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_accept(self, client):
        """
        Test PATCH request to /api/v1/driver/orders/<pk>/accept/
        """
        url = reverse('api:v1:accept-order', args=(self.active_order_1_1.pk, ))

        # send request without token
        response = client.post(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }

        # try to skip order with status != "assigned"
        assignment = OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_1
        )
        response = client.post(url, data=json.dumps({}), **headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'message': 'Current order cannot be accepted at the moment'
        }
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.NEW

        # change order status to `assigned`
        self.active_order_1_1.status = OrderStatus.ASSIGNED
        self.active_order_1_1.save()

        response = client.post(url, data=json.dumps({}), **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'message': 'Order accepted'}

        self.active_order_1_1.refresh_from_db()
        assignment.refresh_from_db()
        assert assignment.status == OrderAssignmentStatus.ACCEPTED
        assert self.active_order_1_1.status == OrderStatus.ACCEPTED
        assert self.active_order_1_1.driver == self.driver

        # try to change order status for the shop he is not member of
        url = reverse('api:v1:accept-order', args=(self.active_order_2_1.pk,))
        response = client.post(url, data=json.dumps({}), **headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_confirm_mpesa(self, client):
        """
        Test PATCH request to /api/v1/driver/orders/<pk>/confirm/
        order is paid via mpesa
        """
        url = reverse('api:v1:confirm-order', args=(self.active_order_1_1.pk, ))

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }

        # try to confirm order with wrong code
        json_data = json.dumps({'verification_code': 'ver_code'})
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [{
            'domain': 'order.error',
            'code': 310,
            'desc': f'Incorrect verification code'
        }]
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.NEW

        # try to confirm order with wrong code
        json_data = json.dumps({'verification_code': 'confcode'})
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'message': 'Order confirmed'}
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.COMPLETED

        # try to change order status for the shop he is not member of
        url = reverse('api:v1:confirm-order', args=(self.active_order_2_1.pk,))
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_confirm_cash(self, client):
        """
        Test PATCH request to /api/v1/driver/orders/<pk>/confirm/
        order is paid with cash
        """
        self.active_order_1_1.payment_method = PaymentMethod.CASH
        self.active_order_1_1.save()

        url = reverse('api:v1:confirm-order', args=(self.active_order_1_1.pk, ))

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }

        # try to confirm order (no code provided)
        json_data = json.dumps({})
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'message': 'Order confirmed'}
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.COMPLETED

        # try to change order status for the shop he is not member of
        url = reverse('api:v1:confirm-order', args=(self.active_order_2_1.pk,))
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_order_pay(self, client, mocker):
        """
        Test POST request to /api/v1/driver/orders/<pk>/pay/
        """
        new_refund_patch = mocker.patch(
            'apps.management.orders.models.Payment.new_submit'
        )
        new_refund_patch.return_value = True

        url = reverse('api:v1:pay-order', args=(self.active_order_1_1.pk,))

        # send request without token
        response = client.post(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }

        self.active_order_1_1.payment_method = PaymentMethod.MPESA
        self.active_order_1_1.save()

        json_data = json.dumps({})
        response = client.post(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'message': 'Paid request sent successfully'
        }
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.verification_required is False

        assert Payment.new_submit.called is True

    def test_order_change(self, client):
        """
        Test PATCH request to /api/v1/driver/orders/
        """
        self.active_order_1_1.status = OrderStatus.NEW
        self.active_order_1_1.save()

        url = reverse('api:v1:driver-order', args=(self.active_order_1_1.pk, ))

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }

        OrderAssignments.objects.filter(order=self.active_order_1_1).delete()

        json_data = json.dumps({'status': OrderStatus.PICKED_UP})
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_200_OK

        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.PICKED_UP

        # try to change related to driver order status
        self.active_order_1_1.status = OrderStatus.ACCEPTED
        self.active_order_1_1.save()

        OrderAssignments.objects.create(
            order=self.active_order_1_1,
            driver=self.driver,
            status=OrderAssignmentStatus.ACCEPTED
        )

        json_data = json.dumps({'status': OrderStatus.PICKED_UP})
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_200_OK
        self.active_order_1_1.refresh_from_db()
        assert self.active_order_1_1.status == OrderStatus.PICKED_UP

        # try to change order status for the shop he is not member of
        url = reverse('api:v1:confirm-order', args=(self.active_order_2_1.pk,))
        response = client.patch(url, data=json_data, **headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_active(self, client):
        """
        Test GET request to /api/v1/driver/orders/ (active orders)
        """
        url = reverse('api:v1:driver-orders-active')

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.inactive_order_1_1
        )
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.inactive_order_1_2
        )

        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_1
        )

        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_1,
            status=OrderAssignmentStatus.ASSIGNED
        )
        # make order - skipped
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_2,
            status=OrderAssignmentStatus.REJECTED
        )
        # make order - accepted
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_3,
            status=OrderAssignmentStatus.ACCEPTED
        )

        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_2_1
        )
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_2_2
        )

        response = client.get(url, **headers)
        assert response.status_code == status.HTTP_200_OK
        orders_numbers = [o['order_number'] for o in response.json()['results']]
        assert self.active_order_1_1.order_number in orders_numbers
        assert self.active_order_1_2.order_number not in orders_numbers
        assert self.active_order_1_3.order_number in orders_numbers
        assert len(orders_numbers) == 2

    def test_list_history(self, client):
        """
        Test GET request to /api/v1/driver/orders/ (history orders)
        """
        url = reverse('api:v1:driver-orders-history')

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.inactive_order_1_1
        )
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.inactive_order_1_2
        )
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_1
        )
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_2
        )
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_2_1
        )
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_2_2
        )

        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.inactive_order_1_1,
            status=OrderAssignmentStatus.ACCEPTED
        )

        response = client.get(url, **headers)
        assert response.status_code == status.HTTP_200_OK
        orders_numbers = [o['order_number'] for o in response.json()['results']]

        assert self.inactive_order_1_1.order_number in orders_numbers
        assert self.inactive_order_1_2.order_number not in orders_numbers
        assert len(orders_numbers) == 1

    def test_retrieve(self, client):
        """
        Test PATCH request to /api/v1/driver/orders/<pk>/
        """
        url = reverse('api:v1:driver-order', args=(self.active_order_1_2.pk,))

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_2
        )

        response = client.get(url, **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'shipping_address': {
                'type': 'Feature',
                'geometry': None,
                'properties': {
                    'address': self.active_order_1_2.shipping_address.address
                }
            },
            'delivery_fee': '{0:.2f}'.format(
                self.active_order_1_2.delivery_fee
            ),
            'buyer_name': self.active_order_1_2.buyer_name,
            'buyer_phone': self.active_order_1_2.buyer_phone,
            'buyer_email': self.active_order_1_2.buyer_email,
            'payment_method': self.active_order_1_2.payment_method,
            'positions': [],
            'warehouse': self.active_order_1_2.warehouse.code,
            'warehouse_location': {
                'code': self.active_order_1_2.warehouse.code,
                'location': {
                    'geometry': {
                        'coordinates': [39.6650254, -4.060742],
                        'type': 'Point'
                    },
                    'properties': {
                        'address': \
                            self.active_order_1_2.warehouse.location.address
                    },
                    'type': 'Feature'
                },
                'name': self.active_order_1_2.warehouse.name
            },
            'order_number': self.active_order_1_2.order_number,
            'is_active': self.active_order_1_2.is_active,
            'id': self.active_order_1_2.id,
            'status_verbose': self.active_order_1_2.status_verbose,
            'is_paid': self.active_order_1_2.is_paid,
            'pending_transaction': self.active_order_1_2.pending_transaction,
            'verification_required': self.active_order_1_2.verification_required,
            'is_payment_link': self.active_order_1_2.is_payment_link,
            'total_amount': '{0:.2f}'.format(
                self.active_order_1_2.total_price()
            )
        }

        # try to get order from the other shop
        url = reverse('api:v1:driver-order', args=(self.active_order_2_1.pk,))
        response = client.get(url, **headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch(self, client):
        """
        Test PATCH request to /api/v1/driver/orders/<pk>/
        """
        url = reverse('api:v1:driver-order', args=(self.active_order_1_2.pk,))

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        OrderAssignments.objects.create(
            driver=self.driver,
            order=self.active_order_1_2
        )
        patch_data = {'status': OrderStatus.CANCELED}
        response = client.patch(url, data=json.dumps(patch_data), **headers)
        assert response.status_code == status.HTTP_200_OK

        self.active_order_1_2.refresh_from_db()
        assert self.active_order_1_2.status == OrderStatus.CANCELED

        # try to edit order from the other shop
        url = reverse('api:v1:driver-order', args=(self.active_order_2_1.pk,))
        response = client.get(url, **headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPasswordChangeEndpoint:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self):

        self.driver_profile = DriverProfileFactory()
        self.driver = self.driver_profile.user

    def test_change_password(self, client):
        """
        Test PUT request to /api/v1/change_password/
        """
        url = reverse('api:v1:change-password')

        # send request without token
        response = client.patch(url)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        put_data = {'password': ''}
        response = client.patch(url, data=json.dumps(put_data), **headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                'domain': 'change_password.error',
                'code': 202,
                'desc': 'password is a required field'
            }
        ]

        put_data = {'password': 'new_password'}
        response = client.patch(url, data=json.dumps(put_data), **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 'Password successfully changed'


class TestPasswordRestoreRequestEndpoint:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self):

        self.driver_profile = DriverProfileFactory()
        self.driver = self.driver_profile.user

    def test_request_password_restore(self, client):
        """
        Test POST request to /api/v1/restore_password_request/
        """
        url = reverse('api:v1:restore-password-request')

        headers = {'content_type': 'application/json'}

        email = 'unexistentemail@example.com'
        post_data = {'email': email}
        response = client.post(url, data=json.dumps(post_data), **headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                'domain': 'restore_password.error',
                'code': 301,
                'desc': f'User with email {email} does not exists'
            }
        ]

        post_data = {'email': self.driver.email}
        response = client.post(url, data=json.dumps(post_data), **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 'New code generated'

    def test_submit_password_restore(self, client):
        """
        Test POST request to /api/v1/restore_password_request/
        """
        request_url = reverse('api:v1:restore-password-request')
        submit_url = reverse('api:v1:restore-password-submit')

        headers = {'content_type': 'application/json'}

        # request password restore
        client.post(
            request_url,
            data=json.dumps({'email': self.driver.email}),
            **headers
        )

        code = client.session.get(f'{self.driver.email}_restore_password_code')

        email = 'unexistentemail@example.com'
        post_data = {
            'email': email,
            'code': code,
            'password': 'new_password'
        }
        response = client.post(
            submit_url,
            data=json.dumps(post_data),
            **headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                'domain': 'restore_password.error',
                'code': 301,
                'desc': f'User with email "{email}" does not exists'
            },
            {
                'domain': 'restore_password.error',
                'code': 401,
                'desc': 'Codes does not match'
            }
        ]

        post_data = {
            'email': self.driver.email,
            'code': 'wrong_code',
            'password': 'new_password'
        }
        response = client.post(
            submit_url,
            data=json.dumps(post_data),
            **headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                'domain': 'restore_password.error',
                'code': 301,
                'desc': f'User with email "{email}" does not exists'
            },
            {
                'domain': 'restore_password.error',
                'code': 401,
                'desc': 'Codes does not match'
            },
            {
                'domain': 'restore_password.error',
                'code': 401,
                'desc': 'Codes does not match'
            }
        ]

        post_data = {
            'email': self.driver.email,
            'code': code,
            'password': 'new_password'
        }
        response = client.post(
            submit_url,
            data=json.dumps(post_data),
            **headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 'Password successfully restored'


class TestChatEndpoint:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.shop_1 = ShopFactory()

        self.driver_profile = DriverProfileFactory()
        self.driver = self.driver_profile.user
        self.driver.shop = self.shop_1
        self.driver.save()

        # active orders
        self.active_order_1_1 = OrderFactory(
            shop=self.shop_1,
            order_number=9,
        )
        self.active_order_1_1.driver = None
        self.active_order_1_1.save()

        self.active_order_1_2 = OrderFactory(
            shop=self.shop_1,
            order_number=5,
            status=OrderStatus.ASSIGNED
        )

        # recent orders
        self.inactive_order_1_1 = OrderFactory(
            shop=self.shop_1,
            order_number=6,
            status=OrderStatus.CANCELED
        )
        self.inactive_order_1_2 = OrderFactory(
            shop=self.shop_1,
            order_number=7,
            status=OrderStatus.COMPLETED
        )

        # shop 2
        self.shop_2 = ShopFactory()

        # active orders (shop 2)
        self.active_order_2_1 = OrderFactory(
            shop=self.shop_2,
            order_number=8,
            status=OrderStatus.ASSIGNED
        )

        # recent orders (shop 2)
        self.active_order_2_2 = OrderFactory(
            shop=self.shop_2,
            order_number=10,
            status=OrderStatus.COMPLETED
        )

    def test_message_send(self, client):
        """
        Test POST request to /api/v1/chat/
        """
        url = reverse('api:v1:chat')

        headers = {'content_type': 'application/json'}

        message = 'Hi there!'
        post_data = {'message': message}

        # send request without token
        response = client.post(url, data=json.dumps(post_data), **headers)
        assert response.status_code == 401
        assert response.json() == {
            'detail': 'Authentication credentials were not provided.'
        }

        # add token to the request
        headers = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.driver.auth_token.key),
            'content_type': 'application/json'
        }
        response = client.post(url, data=json.dumps({}), **headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                'domain': 'chat.error',
                'code': 201,
                'desc': 'message is invalid'
            }
        ]

        response = client.post(url, data=json.dumps(post_data), **headers)
        msg = Message.objects.first()
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == 'Message sent'

