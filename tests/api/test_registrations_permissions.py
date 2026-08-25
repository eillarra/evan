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

    def test_authenticated_user_can_register_with_extra_data(self, api_client, t_event, user) -> None:
        """Registration extra_data payload is persisted when creating a registration."""
        api_client.force_authenticate(user=user)
        payload = {
            "fee_type": "regular",
            "extra_data": {
                "paper_id": "P-123",
                "_internal": {"share_email_with_sponsors": False, "allow_photo_sharing": True},
            },
        }

        response = api_client.post(_register_url(t_event), payload, format="json")

        assert response.status_code == status.CREATED
        assert response.data["extra_data"]["paper_id"] == "P-123"


@pytest.mark.api
class TestRegistrationCreateFeeCap:
    """Registration creation against a capped fee type that is sold out."""

    @pytest.fixture
    def capped_event(self, t_event):
        """Add a capped ``phd`` fee (max 1) to the standard test event."""
        from evan.models import Fee

        Fee.objects.create(event=t_event, type="phd", value=0, config={"max_registrations": 1})
        return t_event

    def test_register_for_capped_fee_when_room_available(self, api_client, capped_event, user) -> None:
        api_client.force_authenticate(user=user)
        response = api_client.post(_register_url(capped_event), {"fee_type": "phd"})
        assert response.status_code == status.CREATED

    def test_register_for_sold_out_capped_fee_returns_400(self, api_client, capped_event, user) -> None:
        """When the cap is reached, a new registration gets a clean 400, not a 500."""
        # Fill the single slot.
        RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

        api_client.force_authenticate(user=user)
        response = api_client.post(_register_url(capped_event), {"fee_type": "phd"})
        assert response.status_code == status.BAD_REQUEST
        assert "non_field_errors" in response.data
        assert "sold out" in str(response.data["non_field_errors"])

    def test_register_for_uncapped_fee_unaffected_by_cap(self, api_client, capped_event, user) -> None:
        """The ``regular`` fee stays available even when ``phd`` is sold out."""
        RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

        api_client.force_authenticate(user=user)
        response = api_client.post(_register_url(capped_event), {"fee_type": "regular"})
        assert response.status_code == status.CREATED


@pytest.mark.api
class TestRegistrationCreateSessionCap:
    """A session-capacity error surfaced via the registration endpoint uses the right key.

    Accompanying-person social-event caps are enforced inside ``Registration.save()``,
    so a full social event raises ``ValueError`` which the view converts into a 400.
    The error must be reported under ``non_field_errors`` (it is not a fee problem),
    never under a misleading ``fee_type`` key.
    """

    def test_full_social_event_returns_400_under_non_field_errors(self, api_client, t_event, user) -> None:
        from evan.models import Session

        social = Session.objects.create(
            event=t_event,
            title="Gala Dinner",
            is_social_event=True,
            max_attendees=1,
        )
        # Fill the single slot.
        RegistrationFactory(
            event=t_event,
            user=UserFactory(),
            fee_type="regular",
            extra_data={"accompanying_persons": [{"name": "Jane", "selected_social_events": [social.id]}]},
        )

        api_client.force_authenticate(user=user)
        response = api_client.post(
            _register_url(t_event),
            {
                "fee_type": "regular",
                "extra_data": {
                    "accompanying_persons": [{"name": "Bob", "selected_social_events": [social.id]}],
                },
            },
            format="json",
        )

        assert response.status_code == status.BAD_REQUEST
        assert "non_field_errors" in response.data
        assert "fee_type" not in response.data
        assert "full" in str(response.data["non_field_errors"])


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

    def test_owner_can_update_registration_extra_data(self, api_client, user, registration) -> None:
        """Owner can PATCH registration extra_data and the new values are persisted."""
        api_client.force_authenticate(user=user)
        payload = {
            "extra_data": {
                "paper_id": "P-456",
                "_internal": {"share_email_with_sponsors": True, "allow_photo_sharing": False},
            }
        }

        response = api_client.patch(_detail_url(registration), payload, format="json")

        assert response.status_code == status.OK
        registration.refresh_from_db()
        assert registration.extra_data["paper_id"] == "P-456"

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

    def test_owner_changing_fee_type_into_sold_out_returns_400(self, api_client, t_event, user) -> None:
        """Switching a registration to a sold-out capped fee is rejected with 400."""
        from evan.models import Fee

        Fee.objects.create(event=t_event, type="phd", value=0, config={"max_registrations": 1})
        # Fill the single slot with another user.
        RegistrationFactory(event=t_event, user=UserFactory(), fee_type="phd")
        # The owner has a `regular` registration.
        own = RegistrationFactory(event=t_event, user=user, fee_type="regular")

        api_client.force_authenticate(user=user)
        response = api_client.patch(_detail_url(own), {"fee_type": "phd"})
        assert response.status_code == status.BAD_REQUEST
        assert "non_field_errors" in response.data
        assert "sold out" in str(response.data["non_field_errors"])

    def test_owner_changing_fee_type_out_of_capped_frees_slot(self, api_client, t_event, user) -> None:
        """Switching away from a capped fee frees the slot and succeeds."""
        from evan.models import Fee

        Fee.objects.create(event=t_event, type="phd", value=0, config={"max_registrations": 1})
        # The owner holds the single `phd` slot.
        own = RegistrationFactory(event=t_event, user=user, fee_type="phd")

        api_client.force_authenticate(user=user)
        response = api_client.patch(_detail_url(own), {"fee_type": "regular"})
        assert response.status_code == status.OK
