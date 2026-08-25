"""Tests for per-session attendee caps (``Session.max_attendees``).

A capped social event refuses new attendees, whether the main registrant or
an accompanying person, once the cap is reached. Rejected registrations do
not count toward the cap. Re-saving a registration that already holds a slot
must not be blocked by its own selection.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from evan.models import Fee, Session
from tests._factories import EventFactory, RegistrationFactory, SessionFactory, UserFactory


def dt(s: str) -> datetime:
    """Parse an ISO-like datetime string into a UTC-aware datetime.

    :param s: A datetime string in ``YYYY-MM-DD HH:MM`` format.
    :returns: A timezone-aware datetime in UTC.
    """
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


@pytest.fixture
def capped_event(db):
    """An event with a capped social event (max 1 attendee) and a regular fee."""
    event = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-03-01 00:00").date(),
        registration_deadline=dt("2026-08-31 23:59"),
        registration_early_deadline=None,
        registration_onsite_deadline=None,
    )
    Fee.objects.create(event=event, type="regular", value=100)
    return event


@pytest.fixture
def social_event(capped_event) -> Session:
    return SessionFactory(event=capped_event, is_social_event=True, max_attendees=1)


def make_registration(event, *, extra_data: dict | None = None) -> object:
    with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
        return RegistrationFactory(event=event, user=UserFactory(), fee_type="regular", extra_data=extra_data or {})


class TestSessionAttendeeCount:
    """``Session.attendee_count`` combines main registrants and accompanying persons."""

    def test_uncapped_session_has_no_remaining_capacity_limit(self, capped_event):
        session = SessionFactory(event=capped_event, is_social_event=True, max_attendees=0)

        assert session.remaining_capacity is None
        assert session.is_full is False

    def test_main_registrant_counts_toward_attendee_count(self, capped_event, social_event):
        registration = make_registration(capped_event)
        registration.sessions.add(social_event)

        social_event.refresh_from_db()
        assert social_event.attendee_count == 1
        assert social_event.remaining_capacity == 0
        assert social_event.is_full is True

    def test_accompanying_person_counts_toward_attendee_count(self, capped_event, social_event):
        make_registration(
            capped_event,
            extra_data={"accompanying_persons": [{"name": "Jane", "selected_social_events": [social_event.id]}]},
        )

        assert social_event.attendee_count == 1
        assert social_event.is_full is True

    def test_rejected_registration_does_not_count(self, capped_event, social_event):
        registration = make_registration(capped_event)
        registration.sessions.add(social_event)
        registration.is_accepted = False
        registration.save()

        assert social_event.attendee_count == 0
        assert social_event.is_full is False


class TestSessionCapEnforcement:
    """A full social event rejects new attendees, main or accompanying."""

    def test_main_registrant_blocked_when_full(self, capped_event, social_event):
        first = make_registration(capped_event)
        first.sessions.add(social_event)

        second = make_registration(capped_event)
        with pytest.raises(ValueError, match="full"):
            second.sessions.add(social_event)

    def test_accompanying_person_blocked_when_full(self, capped_event, social_event):
        first = make_registration(capped_event)
        first.sessions.add(social_event)

        with pytest.raises(ValueError, match="full"):
            make_registration(
                capped_event,
                extra_data={"accompanying_persons": [{"name": "Jane", "selected_social_events": [social_event.id]}]},
            )

    def test_resaving_registration_keeps_its_own_slot(self, capped_event, social_event):
        registration = make_registration(capped_event)
        registration.sessions.add(social_event)

        # Re-adding the same session must not be blocked by its own slot.
        registration.sessions.add(social_event)
        assert social_event.attendee_count == 1

    def test_resaving_accompanying_person_keeps_its_own_slot(self, capped_event, social_event):
        extra_data = {"accompanying_persons": [{"name": "Jane", "selected_social_events": [social_event.id]}]}
        registration = make_registration(capped_event, extra_data=extra_data)

        registration.manual_extra_fees = 10
        registration.save()

        registration.refresh_from_db()
        assert registration.manual_extra_fees == 10
        assert social_event.attendee_count == 1


class TestSessionCapSerializerFields:
    """``SessionReadOnlySerializer`` exposes ``is_full`` and ``remaining_capacity``."""

    def test_uncapped_session_reports_infinite_capacity(self, capped_event, rf):
        from evan.api.serializers import SessionReadOnlySerializer

        session = SessionFactory(event=capped_event, is_social_event=True, max_attendees=0)

        data = SessionReadOnlySerializer(session, context={"request": rf.get("/")}).data
        assert data["remaining_capacity"] is None
        assert data["is_full"] is False

    def test_capped_session_reports_remaining_capacity(self, capped_event, social_event, rf):
        from evan.api.serializers import SessionReadOnlySerializer

        registration = make_registration(capped_event)
        registration.sessions.add(social_event)

        data = SessionReadOnlySerializer(social_event, context={"request": rf.get("/")}).data
        assert data["remaining_capacity"] == 0
        assert data["is_full"] is True
