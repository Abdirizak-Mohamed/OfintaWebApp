# third party
import pytest

# ofinta
from apps.core.models import UserRoles, OfintaUser


@pytest.fixture
def manager(django_db_blocker):
    user = OfintaUser.objects.create(
        email='manager@example.com', role=UserRoles.MANAGER
    )
    user.set_password('password')
    user.save()
    return user


@pytest.fixture
def owner(django_db_blocker):
    user = OfintaUser.objects.create(
        email='owner@example.com', role=UserRoles.OWNER
    )
    user.set_password('password')
    user.save()
    return user
