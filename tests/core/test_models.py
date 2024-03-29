
# third party
import pytest

# ofinta
# ..

# define fixtures
from apps.core.models import OfintaUser


@pytest.mark.django_db
class TestDashboard:
    pytestmark = pytest.mark.django_db

    def test_change_password(self):
        user = OfintaUser.objects.create_user(
            email='user@example.com',
            password='pa$$word'
        )
        assert user.changed_password is False

        user.set_password('new_pa$$word')
        user.save()

        assert user.changed_password is True
