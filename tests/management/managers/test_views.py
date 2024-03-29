# third party
import pytest

# django
from django.urls import reverse

# ofinta
from apps.core.models import UserRoles, OfintaUser
from apps.management.dashboard.tests.factories import ShopFactory, UserFactory


@pytest.mark.django_db
class TestManagers:
    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def setup_test_data(self, manager, owner):
        self.shop_1 = ShopFactory()

        self.owner = owner
        self.owner.shop = self.shop_1
        self.owner.save()

        self.manager = manager
        self.manager.shop = self.shop_1
        self.manager.save()

        self.manager_1_1 = UserFactory(
            role=UserRoles.MANAGER, shop=self.shop_1
        )
        self.manager_1_2 = UserFactory(
            role=UserRoles.MANAGER, shop=self.shop_1
        )
        self.manager_1_3 = UserFactory(
            role=UserRoles.MANAGER, shop=self.shop_1, is_active=False
        )

        # shop 2
        self.shop_2 = ShopFactory()

        self.manager_2_1 = UserFactory(
            role=UserRoles.MANAGER,
            shop=self.shop_2
        )
        self.manager_2_2 = UserFactory(
            role=UserRoles.MANAGER, shop=self.shop_2, is_active=False
        )

    def test_managers_list(self, client):
        url = reverse('management:managers-list')

        # manager has no access to the shop managers
        client.login(email=self.manager.email, password='password')
        response = client.get(url)
        assert response.status_code == 403

        client.logout()

        # owner can access shop managers list
        client.login(email=self.owner.email, password='password')

        response = client.get(url)
        assert response.status_code == 200
        context = response.context

        assert self.manager_1_1 in context['managers']
        assert self.manager_1_2 in context['managers']
        assert self.manager_1_3 in context['managers']

        # managers from the other shop not shown
        assert self.manager_2_1 not in context['managers']
        assert self.manager_2_2 not in context['managers']

    def test_manager_details(self, client):
        url = reverse(
            'management:manager-details', args=(self.manager_1_1.pk, )
        )

        # manager has no access to the shop manager
        client.login(email=self.manager.email, password='password')
        response = client.get(url)
        assert response.status_code == 403

        client.logout()

        # owner can access shop manager
        client.login(email=self.owner.email, password='password')

        response = client.get(url)
        assert response.status_code == 200
        context = response.context

        assert self.manager_1_1 == context['manager']

        # owner has no access to the other shops managers

        url = reverse(
            'management:manager-details', args=(self.manager_2_1.pk, )
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_manager_create(self, client):
        url = reverse('management:manager-add')

        # manager cannot create other shop managers
        client.login(email=self.manager.email, password='password')
        response = client.post(url, {})
        assert response.status_code == 403

        client.logout()

        # owner can create shop managers
        client.login(email=self.owner.email, password='password')

        managers_before = OfintaUser.objects.filter(
            role=UserRoles.MANAGER
        ).count()
        post_data = {
            'first_name': 'Ibrahim',
            'last_name': 'Azikiwe',
            'email': 'ibrahim.azikiwe@example.com',
            'role': UserRoles.MANAGER,
            'shop': self.shop_1.pk
        }
        response = client.post(url, post_data)
        managers_after = OfintaUser.objects.filter(
            role=UserRoles.MANAGER
        ).count()
        assert response.url == reverse('management:managers-list')
        assert response.status_code == 302

        new_manager = OfintaUser.objects.filter(role=UserRoles.MANAGER).last()
        assert new_manager.first_name == 'Ibrahim'
        assert new_manager.last_name == 'Azikiwe'
        assert new_manager.email == 'ibrahim.azikiwe@example.com'
        assert new_manager.role == UserRoles.MANAGER
        assert new_manager.shop == self.shop_1

        assert managers_before + 1 == managers_after

        # owner cannot create managers for the shops he is not owner
        managers_before = OfintaUser.objects.filter(
            role=UserRoles.MANAGER
        ).count()
        post_data['shop'] = self.shop_2.pk
        response = client.post(url, post_data)
        managers_after = OfintaUser.objects.filter(
            role=UserRoles.MANAGER
        ).count()
        assert response.context['form'].is_valid() is False
        assert response.status_code == 200
        assert managers_before == managers_after

    def test_manager_edit(self, client):
        url = reverse(
            'management:manager-edit', args=(self.manager_1_1.pk, )
        )

        # manager cannot edit other shop managers
        client.login(email=self.manager.email, password='password')
        response = client.post(url, {})
        assert response.status_code == 403

        client.logout()

        # owner can edit shop managers
        client.login(email=self.owner.email, password='password')

        post_data = {
            'first_name': 'Ibrahim',
            'last_name': 'Azikiwe',
            'email': 'ibrahim.azikiwe@example.com',
            'role': UserRoles.MANAGER,
            'shop': self.shop_1.pk
        }
        response = client.post(url, post_data)
        assert response.status_code == 302
        assert response.url == reverse(
            'management:manager-details', args=(self.manager_1_1.pk, )
        )
        self.manager_1_1.refresh_from_db()
        assert self.manager_1_1.first_name == 'Ibrahim'

        # owner cannot move manager to the shops he is not owner
        url = reverse(
            'management:manager-edit', args=(self.manager_2_1.pk, )
        )
        post_data['first_name'] = 'Ibrahim (new)'
        post_data['shop'] = self.shop_2.pk
        response = client.post(url, post_data)
        assert response.status_code == 404

    def test_manager_status(self, client):
        url = reverse(
            'management:manager-status', args=(self.manager_1_1.pk, )
        )

        # manager cannot change shop managers statuses
        client.login(email=self.manager.email, password='password')
        response = client.post(url, {})
        assert response.status_code == 403

        client.logout()

        # owner can change shop managers status
        client.login(email=self.owner.email, password='password')

        response = client.post(url, {})
        assert response.status_code == 302
        assert response.url == reverse(
            'management:manager-details', args=(self.manager_1_1.pk, )
        )
        self.manager_1_1.refresh_from_db()
        assert self.manager_1_1.is_active == False

        response = client.post(url, {})
        assert response.status_code == 302
        self.manager_1_1.refresh_from_db()
        assert self.manager_1_1.is_active == True

        # owner cannot change manager status from the shops he is not owner
        url = reverse(
            'management:manager-edit', args=(self.manager_2_1.pk, )
        )
        response = client.post(url, {})
        assert response.status_code == 404

    def test_manager_remove(self, client):
        url = reverse(
            'management:manager-remove', args=(self.manager_1_1.pk, )
        )

        # manager cannot change shop managers statuses
        client.login(email=self.manager.email, password='password')
        response = client.post(url, {})
        assert response.status_code == 403

        client.logout()

        # owner can remove shop managers status
        client.login(email=self.owner.email, password='password')

        response = client.post(url, {})
        assert response.status_code == 302
        assert response.url == reverse('management:managers-list')
        assert OfintaUser.objects.filter(
            pk=self.manager_1_1.pk
        ).exists() is False

        # owner cannot remove manager from the shops he is not owner
        url = reverse(
            'management:manager-remove', args=(self.manager_2_1.pk, )
        )
        response = client.post(url, {})
        assert response.status_code == 404
