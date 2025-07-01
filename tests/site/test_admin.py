from http import HTTPStatus as status

import pytest
from django.urls import reverse

from tests._factories import UserFactory


@pytest.fixture
def admin(db):
    return UserFactory(is_staff=True)


@pytest.fixture
def superuser(db):
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.site
class TestForAnonymous:
    expected_status_codes: dict[str, status] = {
        "admin_index": status.FOUND,
    }

    def test_admin_index(self, client):
        response = client.get(reverse("admin:index"))
        assert response.status_code == self.expected_status_codes["admin_index"]


class TestForAuthenticated(TestForAnonymous):
    expected_status_codes: dict[str, status] = {
        "admin_index": status.FOUND,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, user):
        client.force_login(user=user)


class TestForAdmin(TestForAuthenticated):
    expected_status_codes: dict[str, status] = {
        "admin_index": status.OK,
        "admin_pages": status.FORBIDDEN,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, admin):
        client.force_login(user=admin)

    @pytest.mark.parametrize(
        "route",
        [
            "admin:evan_event",
            "admin:evan_registration",
        ],
    )
    def test_admin_pages(self, client, route, t_event):
        response = client.get(reverse(f"{route}_changelist"))
        assert response.status_code == self.expected_status_codes["admin_pages"]
        response = client.get(reverse(f"{route}_add"))
        assert response.status_code == self.expected_status_codes["admin_pages"]


class TestForSuperuser(TestForAdmin):
    expected_status_codes: dict[str, status] = {
        "admin_index": status.OK,
        "admin_pages": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, superuser):
        client.force_login(user=superuser)
