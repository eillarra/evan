from http import HTTPStatus as status

import pytest
from django.urls import reverse

from tests._factories import EventFactory, UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.site
class TestForAnonymous:
    """Anonymous visitors see listed public pages and are sent to login for the console."""

    expected_status_codes: dict[str, status] = {
        "homepage": status.OK,
        "event:app_listed": status.OK,
        "event:app_unlisted": status.NOT_FOUND,
        "event:manage": status.FOUND,
    }

    def test_homepage_access(self, client, db):
        response = client.get(reverse("homepage"))
        assert response.status_code == self.expected_status_codes["homepage"]

    def test_public_page_listed(self, client, t_event):
        response = client.get(reverse("event:app", args=[t_event.code]))
        assert response.status_code == self.expected_status_codes["event:app_listed"]

    def test_public_page_unlisted(self, client, db):
        event = EventFactory(code="pending-event", listing_status="pending_review")
        response = client.get(reverse("event:app", args=[event.code]))
        assert response.status_code == self.expected_status_codes["event:app_unlisted"]

    def test_manage_redirects_to_login(self, client, t_event):
        response = client.get(reverse("event:manage", args=[t_event.code]))
        assert response.status_code == self.expected_status_codes["event:manage"]


class TestForAuthenticated(TestForAnonymous):
    """Authenticated non-managers see the public page but not the console."""

    expected_status_codes: dict[str, status] = {
        "homepage": status.OK,
        "event:app_listed": status.OK,
        "event:app_unlisted": status.NOT_FOUND,
        "event:manage": status.FORBIDDEN,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, user):
        client.force_login(user=user)


class TestForEventManager(TestForAuthenticated):
    """Managers see unlisted events on the public page and can open the console."""

    expected_status_codes: dict[str, status] = {
        "homepage": status.OK,
        "event:app_listed": status.OK,
        "event:app_unlisted": status.OK,
        "event:manage": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, t_event_manager):
        client.force_login(user=t_event_manager)

    def test_public_page_unlisted(self, client, db):
        """An unlisted event stays hidden from managers of other events."""
        event = EventFactory(code="pending-other", listing_status="pending_review")
        response = client.get(reverse("event:app", args=[event.code]))
        assert response.status_code == status.NOT_FOUND

    def test_public_page_unlisted_manager_of_this_event(self, client, db, t_event_manager):
        """A manager of the pending event itself can open its public page."""
        from evan.models.rel.permissions import Permission

        event = EventFactory(code="pending-managed", listing_status="pending_review")
        event.acl.create(user=t_event_manager, level=Permission.ADMIN)

        response = client.get(reverse("event:app", args=[event.code]))
        assert response.status_code == self.expected_status_codes["event:app_unlisted"]
