"""Behaviour tests for the attendee-facing registration API.

Covers:
  1. Payment, invoicing and attendance fields staying read-only for attendees,
     on both ``POST /events/{code}/register/`` and ``PUT/PATCH /registrations/{uuid}/``.
  2. The registration window (``Event.is_open_for_registration``) on API create.
"""

from datetime import UTC, date, datetime, timedelta
from http import HTTPStatus as status

import pytest
from django.urls import reverse

from evan.models import Fee, Registration
from tests._factories import EventFactory, RegistrationFactory, UserFactory


PROTECTED_FIELD_VALUES: dict[str, object] = {
    "paid_via_invoice": 100,
    "manual_extra_fees": 50,
    "invoice_requested": True,
    "invoice_sent": True,
    "invoice_address": "Somewhere 1",
    "payid": "PAY-1",
    "no_show": True,
    "unique_hash": "abcd1234",
    "visa_sent": True,
    "is_accepted": False,
    "tags": ["vip"],
}


@pytest.fixture
def user(db):
    """A regular authenticated user with no special permissions."""
    return UserFactory()


@pytest.fixture
def open_event(db):
    """A listed event whose registration window is currently open, with a ``regular`` fee of 100."""
    event = EventFactory(
        registration_start_date=date.today() - timedelta(days=1),
        registration_deadline=datetime.now(UTC) + timedelta(days=30),
        registration_early_deadline=None,
        registration_onsite_deadline=None,
    )
    Fee.objects.create(event=event, type="regular", value=100)
    return event


@pytest.fixture
def registration(open_event, user):
    """An unpaid registration owned by the regular user fixture."""
    return RegistrationFactory(event=open_event, user=user)


def _register_url(event) -> str:
    return reverse("v1:register-list", args=[event.code])


def _detail_url(registration) -> str:
    return reverse("v1:registration-detail", kwargs={"uuid": str(registration.uuid)})


def _field_snapshot(registration: Registration) -> dict[str, object]:
    registration.refresh_from_db()
    return {field: getattr(registration, field) for field in PROTECTED_FIELD_VALUES}


# ---------------------------------------------------------------------------
# 1. Read-only fields for attendees
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestRegistrationUpdateReadOnlyFields:
    """An owner cannot change staff-managed fields on their own registration."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)

    @pytest.mark.parametrize(("field", "value"), PROTECTED_FIELD_VALUES.items())
    def test_patch_of_protected_field_is_ignored(self, api_client, registration, field, value) -> None:
        before = _field_snapshot(registration)
        saldo_before = registration.saldo

        response = api_client.patch(_detail_url(registration), {field: value}, format="json")

        assert response.status_code == status.OK
        assert _field_snapshot(registration) == before
        assert registration.saldo == saldo_before == -100
        assert registration.is_paid is False

    def test_put_of_retrieved_payload_keeps_protected_fields(self, api_client, registration) -> None:
        """The registration app PUTs back the full object it retrieved; only attendee fields apply."""
        before = _field_snapshot(registration)
        payload = api_client.get(_detail_url(registration)).data
        payload.update(PROTECTED_FIELD_VALUES)
        payload["visa_requested"] = True
        payload["extra_data"] = {"paper_id": "P-1"}

        response = api_client.put(_detail_url(registration), payload, format="json")

        assert response.status_code == status.OK
        assert _field_snapshot(registration) == before
        assert registration.saldo == -100
        assert registration.visa_requested is True
        assert registration.extra_data == {"paper_id": "P-1"}


@pytest.mark.api
class TestRegistrationCreateReadOnlyFields:
    """Staff-managed fields sent on self-registration are ignored."""

    def test_protected_fields_are_ignored_on_create(self, api_client, open_event, user) -> None:
        api_client.force_authenticate(user=user)
        payload = {"fee_type": "regular", "visa_requested": True, **PROTECTED_FIELD_VALUES}

        response = api_client.post(_register_url(open_event), payload, format="json")

        assert response.status_code == status.CREATED
        registration = open_event.registrations.get(user=user)
        assert registration.paid_via_invoice == 0
        assert registration.manual_extra_fees == 0
        assert registration.invoice_requested is False
        assert registration.invoice_sent is False
        assert registration.invoice_address == ""
        assert registration.payid == ""
        assert registration.no_show is False
        assert registration.unique_hash != "abcd1234"
        assert registration.visa_sent is False
        assert registration.is_accepted is True
        assert registration.tags != ["vip"]
        assert registration.saldo == -100
        assert registration.visa_requested is True


# ---------------------------------------------------------------------------
# 2. Registration window
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestRegistrationCreateWindow:
    """API self-registration honours the event's registration window, like the site view."""

    @pytest.mark.parametrize(
        ("start_offset_days", "deadline_offset_days"),
        [
            pytest.param(-30, -1, id="deadline-passed"),
            pytest.param(5, 30, id="not-yet-open"),
        ],
    )
    def test_create_outside_window_is_refused(
        self, api_client, open_event, user, start_offset_days, deadline_offset_days
    ) -> None:
        open_event.registration_start_date = date.today() + timedelta(days=start_offset_days)
        open_event.registration_deadline = datetime.now(UTC) + timedelta(days=deadline_offset_days)
        open_event.save()
        api_client.force_authenticate(user=user)

        response = api_client.post(_register_url(open_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.FORBIDDEN
        assert not open_event.registrations.filter(user=user).exists()

    def test_create_during_onsite_window_is_accepted(self, api_client, open_event, user) -> None:
        open_event.registration_deadline = datetime.now(UTC) - timedelta(days=1)
        open_event.registration_onsite_deadline = datetime.now(UTC) + timedelta(days=1)
        open_event.save()
        api_client.force_authenticate(user=user)

        response = api_client.post(_register_url(open_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.CREATED

    def test_manager_cannot_create_after_deadline(self, api_client, open_event) -> None:
        """The site view has no manager exemption for the window, so neither does the API."""
        from evan.models.rel.permissions import Permission

        manager = UserFactory()
        open_event.acl.create(user=manager, level=Permission.ADMIN)
        open_event.registration_deadline = datetime.now(UTC) - timedelta(days=1)
        open_event.save()
        api_client.force_authenticate(user=manager)

        response = api_client.post(_register_url(open_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.FORBIDDEN
