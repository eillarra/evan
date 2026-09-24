"""Tests for the listing moderation flow: notifications, decisions, transitions."""

from http import HTTPStatus as status

import pytest
from django.test import RequestFactory
from django.urls import reverse

from evan.api.serializers.events import ManagedEventSerializer
from evan.models import EmailLog, Event
from evan.services.listing import PLATFORM_TEAM_EMAIL, record_listing_decision
from tests._factories import EventFactory, UserFactory


def _manager_on(event):
    """Create a manager user on the event's ACL.

    :param event: The event to manage.
    :returns: The manager user.
    """
    from evan.models.rel.permissions import Permission

    manager = UserFactory()
    event.acl.create(user=manager, level=Permission.ADMIN)
    return manager


def _listing_logs() -> list[EmailLog]:
    return list(EmailLog.objects.filter(tags__icontains="type:listing"))


@pytest.mark.django_db
class TestCreationNotification:
    """Creating an event notifies the platform team."""

    def test_created_event_schedules_team_notification(self):
        event = EventFactory()

        logs = _listing_logs()

        assert len(logs) == 1
        assert logs[0].to == [PLATFORM_TEAM_EMAIL]
        assert event.name in logs[0].subject
        assert event.code in logs[0].body
        assert logs[0].event is None

    def test_saving_existing_event_does_not_renotify(self):
        event = EventFactory()
        event.name = "Renamed"
        event.save()

        assert len(_listing_logs()) == 1


@pytest.mark.django_db
class TestListingDecisions:
    """Platform-team decisions are recorded and communicated to organizers."""

    def test_list_event_records_decision_and_notifies_organizers(self):
        event = EventFactory()
        organizer = _manager_on(event)
        staff = UserFactory(is_staff=True)

        record_listing_decision(event, decided_by=staff, decision=Event.ListingStatus.LISTED)

        event.refresh_from_db()
        assert event.listing_status == "listed"
        assert event.listing_decided_by == staff
        assert event.listing_decided_at is not None
        assert event.is_listed is True

        organizer_logs = [log for log in _listing_logs() if organizer.email in log.to]
        assert len(organizer_logs) == 1
        assert "listed" in organizer_logs[0].subject

    def test_decline_event_records_reason_and_notifies_organizers(self):
        event = EventFactory()
        organizer = _manager_on(event)
        staff = UserFactory(is_staff=True)

        record_listing_decision(
            event, decided_by=staff, decision=Event.ListingStatus.DECLINED, reason="Not UGent-related"
        )

        event.refresh_from_db()
        assert event.listing_status == "declined"
        assert event.decline_reason == "Not UGent-related"
        assert event.is_listed is False

        organizer_logs = [log for log in _listing_logs() if organizer.email in log.to]
        assert len(organizer_logs) == 1
        assert "declined" in organizer_logs[0].subject
        assert "Not UGent-related" in organizer_logs[0].body


@pytest.mark.django_db
class TestOrganizerEditsReturnDeclinedToReview:
    """Organizer saves on a declined event return it to review; admin saves do not."""

    def test_organizer_api_edit_returns_declined_event_to_review(self, api_client):
        event = EventFactory(listing_status="declined")
        manager = _manager_on(event)
        api_client.force_authenticate(user=manager)

        response = api_client.patch(reverse("v1:event-detail", args=[event.code]), {"name": "Improved"}, format="json")

        assert response.status_code == status.OK
        event.refresh_from_db()
        assert event.listing_status == "pending_review"

        team_logs = [log for log in _listing_logs() if log.to == [PLATFORM_TEAM_EMAIL]]
        assert len(team_logs) == 2  # creation + re-notification
        assert "again" in team_logs[-1].body

    def test_organizer_edit_of_pending_event_renotifies_team(self, api_client):
        event = EventFactory(listing_status="pending_review")
        manager = _manager_on(event)
        api_client.force_authenticate(user=manager)

        response = api_client.patch(reverse("v1:event-detail", args=[event.code]), {"name": "Improved"}, format="json")

        assert response.status_code == status.OK
        event.refresh_from_db()
        assert event.listing_status == "pending_review"
        assert len([log for log in _listing_logs() if log.to == [PLATFORM_TEAM_EMAIL]]) == 2

    def test_direct_model_save_does_not_transition(self):
        """Platform-team admin saves bypass the API and keep the declined status."""
        event = EventFactory(listing_status="declined")
        event.name = "Admin fixed"
        event.save()

        event.refresh_from_db()
        assert event.listing_status == "declined"


@pytest.mark.django_db
class TestManagedEventSerializerExposure:
    """The managed serializer exposes modules and the listing fields to the console."""

    def test_modules_and_listing_fields_exposed(self):
        event = EventFactory(config={"modules": {"payments": True}})
        event.refresh_from_db()
        request = RequestFactory().get("/")

        data = ManagedEventSerializer(event, context={"request": request}).data

        assert data["modules"] == {
            "payments": True,
            "content": False,
            "program": False,
            "papers": False,
            "communications": False,
        }
        assert data["registration_audience"] == "public"
        assert data["listing_status"] == "listed"
        assert "decline_reason" in data
