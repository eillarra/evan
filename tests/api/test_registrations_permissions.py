"""Tests for registration API endpoint permissions.

Three distinct endpoint groups, each with different access rules:

  1. RegistrationsViewSet  → GET /events/{code}/registrations/
     Event managers list all registrations for their event.
     Attendees are never allowed to see each other's data.

  2. RegistrationCreateViewSet → POST /events/{code}/register/
     Any authenticated user may register for an event once.
     Anonymous users and duplicate registrations are rejected.

  3. RegistrationViewSet → GET/PUT /registrations/{uuid}/
     Each attendee can only access their own registration.
"""

from http import HTTPStatus as status

import pytest
from django.urls import reverse

from tests._factories import RegistrationFactory, UserFactory


@pytest.fixture
def user(db):
    """A regular authenticated user with no special permissions."""
    return UserFactory()


@pytest.fixture
def other_user(db):
    """A second user, used for ownership boundary tests."""
    return UserFactory()


@pytest.fixture
def registration(db, t_event, user):
    """A registration owned by the regular user fixture."""
    return RegistrationFactory(event=t_event, user=user)


def _list_url(event) -> str:
    return event.get_api_url() + "registrations/"


def _register_url(event) -> str:
    return event.get_api_url() + "register/"


def _detail_url(registration) -> str:
    return reverse("v1:registration-detail", kwargs={"uuid": str(registration.uuid)})


# ---------------------------------------------------------------------------
# 1. Manager-only registration list
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestRegistrationsListForAnonymous:
    """The registration list is only for event managers — everyone else is blocked."""

    expected_status_codes: dict[str, status] = {
        "list": status.FORBIDDEN,
    }

    def test_list(self, api_client, t_event) -> None:
        response = api_client.get(_list_url(t_event))
        assert response.status_code == self.expected_status_codes["list"]


class TestRegistrationsListForAuthenticated(TestRegistrationsListForAnonymous):
    """Authenticated attendees cannot list other users' registrations."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestRegistrationsListForEventManager(TestRegistrationsListForAuthenticated):
    """Event managers see all registrations for their event."""

    expected_status_codes = {
        "list": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_list_contains_registrations(self, api_client, t_event, registration) -> None:
        """Registrations belonging to the event appear in the list."""
        response = api_client.get(_list_url(t_event))
        uuids = [r["uuid"] for r in response.data]
        assert str(registration.uuid) in uuids


# ---------------------------------------------------------------------------
# 2. Self-registration
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestRegistrationCreate:
    """Registration creation endpoint requires authentication."""

    def test_anonymous_cannot_register(self, api_client, t_event) -> None:
        response = api_client.post(_register_url(t_event), {"fee_type": "regular"})
        assert response.status_code == status.FORBIDDEN

    def test_authenticated_user_can_register(self, api_client, t_event, user) -> None:
        api_client.force_authenticate(user=user)
        response = api_client.post(_register_url(t_event), {"fee_type": "regular"})
        assert response.status_code == status.CREATED

    def test_duplicate_registration_is_rejected(self, api_client, t_event, user, registration) -> None:
        """A user attempting to register twice for the same event receives a 400."""
        api_client.force_authenticate(user=user)
        response = api_client.post(_register_url(t_event), {"fee_type": "regular"})
        assert response.status_code == status.BAD_REQUEST

    def test_invalid_fee_type_is_rejected(self, api_client, t_event, user) -> None:
        """A fee_type that doesn't exist on the event is rejected."""
        api_client.force_authenticate(user=user)
        response = api_client.post(_register_url(t_event), {"fee_type": "nonexistent_fee"})
        assert response.status_code == status.BAD_REQUEST


# ---------------------------------------------------------------------------
# 3. Registration owner access
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestRegistrationOwnerAccess:
    """Attendees can only retrieve and update their own registration."""

    def test_owner_can_retrieve_own_registration(self, api_client, user, registration) -> None:
        api_client.force_authenticate(user=user)
        response = api_client.get(_detail_url(registration))
        assert response.status_code == status.OK

    def test_owner_sees_event_details_in_registration(self, api_client, user, registration) -> None:
        """The registration detail includes the nested event object."""
        api_client.force_authenticate(user=user)
        response = api_client.get(_detail_url(registration))
        assert "event" in response.data

    def test_non_owner_cannot_retrieve_registration(self, api_client, other_user, registration) -> None:
        """A different authenticated user cannot view someone else's registration."""
        api_client.force_authenticate(user=other_user)
        response = api_client.get(_detail_url(registration))
        assert response.status_code == status.FORBIDDEN

    def test_anonymous_cannot_retrieve_registration(self, api_client, registration) -> None:
        response = api_client.get(_detail_url(registration))
        assert response.status_code == status.FORBIDDEN

    def test_owner_can_update_own_registration(self, api_client, user, registration) -> None:
        """Owner can PATCH mutable fields on their registration."""
        api_client.force_authenticate(user=user)
        response = api_client.patch(_detail_url(registration), {"visa_requested": True})
        assert response.status_code == status.OK

    def test_non_owner_cannot_update_registration(self, api_client, other_user, registration) -> None:
        api_client.force_authenticate(user=other_user)
        response = api_client.patch(_detail_url(registration), {"visa_requested": True})
        assert response.status_code == status.FORBIDDEN

    def test_event_manager_cannot_update_via_registration_endpoint(
        self, api_client, t_event_manager, registration
    ) -> None:
        """The /registrations/{uuid}/ endpoint enforces owner-only access.
        Managers must use the event-scoped registration view (future work)."""
        api_client.force_authenticate(user=t_event_manager)
        response = api_client.patch(_detail_url(registration), {"visa_requested": True})
        assert response.status_code == status.FORBIDDEN
