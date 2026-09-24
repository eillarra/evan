"""Tests for the event listing moderation in the Django admin."""

from http import HTTPStatus as status

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from evan.models import Event
from tests._factories import EventFactory, UserFactory


@pytest.fixture
def superuser(db):
    """Create a superuser for admin testing."""
    User = get_user_model()
    return User.objects.create_superuser("admin", "admin@test.com", "password")


@pytest.fixture
def pending_event(db):
    return EventFactory(code="pending-evt", listing_status="pending_review")


def _changelist_url() -> str:
    return reverse("admin:evan_event_changelist")


def _apply_action(client, action: str, event) -> None:
    """Post an admin action for the given event through the changelist."""
    client.post(
        _changelist_url(),
        {"action": action, "_selected_action": [event.pk]},
        follow=True,
    )


@pytest.mark.site
@pytest.mark.django_db
class TestListingModerationAdmin:
    """Staff-only listing decisions through the Django admin."""

    def test_non_staff_cannot_apply_actions(self, client, pending_event):
        client.force_login(user=UserFactory())

        response = client.post(
            _changelist_url(),
            {"action": "list_events", "_selected_action": [pending_event.pk]},
        )

        assert response.status_code == status.FOUND
        pending_event.refresh_from_db()
        assert pending_event.listing_status == "pending_review"

    def test_list_action_records_decision_fields(self, client, superuser, pending_event):
        client.force_login(user=superuser)
        _apply_action(client, "list_events", pending_event)

        pending_event.refresh_from_db()
        assert pending_event.listing_status == "listed"
        assert pending_event.is_listed is True
        assert pending_event.listing_decided_by == superuser
        assert pending_event.listing_decided_at is not None

    def test_decline_action_records_reason_and_notifies(self, client, superuser, pending_event):
        from evan.models import EmailLog
        from evan.models.rel.permissions import Permission

        organizer = UserFactory()
        pending_event.acl.create(user=organizer, level=Permission.ADMIN)
        client.force_login(user=superuser)

        # The action redirects to the decline confirmation view; apply the decision there.
        response = client.post(
            _changelist_url(),
            {"action": "decline_events", "_selected_action": [pending_event.pk]},
        )
        assert response.status_code == status.FOUND

        response = client.post(
            reverse("admin:evan_event_decline"),
            {"ids": str(pending_event.pk), "reason": "Not UGent-related"},
            follow=True,
        )
        assert response.status_code == status.OK

        pending_event.refresh_from_db()
        assert pending_event.listing_status == "declined"
        assert pending_event.decline_reason == "Not UGent-related"
        assert pending_event.listing_decided_by == superuser

        decline_logs = [log for log in EmailLog.objects.filter(to=[organizer.email]) if "declined" in log.subject]
        assert len(decline_logs) == 1
        assert "Not UGent-related" in decline_logs[0].body

    def test_decline_view_requires_reason(self, client, superuser, pending_event):
        client.force_login(user=superuser)

        response = client.post(
            reverse("admin:evan_event_decline"),
            {"ids": str(pending_event.pk), "reason": ""},
        )

        # The form re-renders with an error; no decision is recorded.
        pending_event.refresh_from_db()
        assert pending_event.listing_status == "pending_review"

    def test_decline_action_is_gettable_with_confirmation_form(self, client, superuser, pending_event):
        client.force_login(user=superuser)

        response = client.get(reverse("admin:evan_event_decline"), {"ids": str(pending_event.pk)})

        assert response.status_code == status.OK
        assert b"reason" in response.content.lower()
