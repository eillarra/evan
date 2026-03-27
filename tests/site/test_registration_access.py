"""Tests for registration site view access by user role.

Two distinct view groups, each with different access rules:

  1. ``RegistrationView``               → GET /r/<code>/
     Any authenticated user can access an event open for registration.
     Closed events without a prior registration raise 403.

  2. ``EventRegistrationPreviewView``   → GET /e/<code>/registration-preview/
     Only event managers may preview the registration form.
"""

from datetime import UTC, date, datetime, timedelta
from http import HTTPStatus as status

import pytest
from django.urls import reverse

from evan.models import Fee
from evan.models.rel.permissions import Permission
from tests._factories import EventFactory, UserFactory


@pytest.fixture
def user(db):
    """A regular authenticated user with no special permissions."""
    return UserFactory()


@pytest.fixture
def open_event(db):
    """An event whose registration window is currently open."""
    event = EventFactory(
        registration_start_date=date.today() - timedelta(days=1),
        registration_deadline=datetime.now(UTC) + timedelta(days=30),
    )
    Fee.objects.create(event=event, type="regular", value=100)
    return event


@pytest.fixture
def open_event_manager(db, open_event):
    """A user with manager-level access on the open event."""
    manager = UserFactory()
    open_event.acl.create(user=manager, level=Permission.ADMIN)
    return manager


def _registration_url(event) -> str:
    return reverse("registration:app", args=[event.code])


def _preview_url(event) -> str:
    return reverse("event:registration_preview", args=[event.code])


# ---------------------------------------------------------------------------
# 1. RegistrationView
# ---------------------------------------------------------------------------


@pytest.mark.site
class TestRegistrationViewForAnonymous:
    """Anonymous users are redirected to the login page."""

    expected_status_codes: dict[str, status] = {
        "app": status.FOUND,
    }

    def test_access(self, client, open_event) -> None:
        response = client.get(_registration_url(open_event))
        assert response.status_code == self.expected_status_codes["app"]


class TestRegistrationViewForAuthenticated(TestRegistrationViewForAnonymous):
    """Authenticated users can access events that are open for registration."""

    expected_status_codes: dict[str, status] = {
        "app": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, user) -> None:
        client.force_login(user=user)

    def test_closed_event_without_registration_is_forbidden(self, client, t_event) -> None:
        """Users who have never registered cannot open a not-yet-open event."""
        response = client.get(_registration_url(t_event))
        assert response.status_code == status.FORBIDDEN


# ---------------------------------------------------------------------------
# 2. EventRegistrationPreviewView
# ---------------------------------------------------------------------------


@pytest.mark.site
class TestRegistrationPreviewForAnonymous:
    """Anonymous users are redirected to the login page."""

    expected_status_codes: dict[str, status] = {
        "preview": status.FOUND,
    }

    def test_access(self, client, t_event) -> None:
        response = client.get(_preview_url(t_event))
        assert response.status_code == self.expected_status_codes["preview"]


class TestRegistrationPreviewForAuthenticated(TestRegistrationPreviewForAnonymous):
    """Regular authenticated users (non-managers) are denied."""

    expected_status_codes: dict[str, status] = {
        "preview": status.FORBIDDEN,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, user) -> None:
        client.force_login(user=user)


class TestRegistrationPreviewForEventManager(TestRegistrationPreviewForAuthenticated):
    """Event managers can preview the registration form regardless of whether registration is open."""

    expected_status_codes: dict[str, status] = {
        "preview": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, t_event_manager) -> None:
        client.force_login(user=t_event_manager)

    def test_preview_works_even_when_registration_is_closed(self, client, t_event) -> None:
        """Managers can preview a form even when registration is not yet open."""
        response = client.get(_preview_url(t_event))
        assert response.status_code == status.OK
