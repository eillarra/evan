from http import HTTPStatus as status

import pytest
from django.urls import reverse

from evan.utils.factories import (
    UserFactory,
)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.site
class TestForAnonymous:
    expected_status_codes: dict[str, status] = {
        "homepage": status.OK,
        "event:app": status.FOUND,
    }

    def test_homepage_access(self, client):
        response = client.get(reverse("homepage"))
        assert response.status_code == self.expected_status_codes["homepage"]

    def test_event_app_access(self, client, test_event):
        response = client.get(reverse("event:app", args=[test_event.code]))
        assert response.status_code == self.expected_status_codes["event:app"]


class TestForAuthenticated(TestForAnonymous):
    expected_status_codes: dict[str, status] = {
        "homepage": status.OK,
        "event:app": status.FORBIDDEN,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, user):
        client.force_login(user=user)


class TestForEventManager(TestForAuthenticated):
    expected_status_codes: dict[str, status] = {
        "homepage": status.OK,
        "event:app": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, test_event_manager):
        client.force_login(user=test_event_manager)


"""
class TestForAttendee(TestForAuthenticated):
    @pytest.fixture(autouse=True)
    def setup(self, client, contact):
        client.force_login(user=contact.user)
"""
