"""Tests for session group exclusivity (``SessionExtraData.group``).

Sessions sharing the same ``extra_data.group`` value are mutually exclusive:
a registrant may pick at most one session per group. The backend enforces this
in the ``sessions`` M2M ``pre_add`` signal alongside the existing capacity
check. Sessions without a group remain freely multi-selectable.
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
def grouped_event(db):
    """An event with a regular fee and a group of mutually-exclusive tours."""
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


def grouped_session(event, *, group: str, title: str = "Tour", max_attendees: int = 0) -> Session:
    """Create a social event session in the given mutual-exclusivity group."""
    return SessionFactory(
        event=event,
        title=title,
        is_social_event=True,
        max_attendees=max_attendees,
        extra_data={"group": group},
    )


def make_registration(event) -> object:
    with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
        return RegistrationFactory(event=event, user=UserFactory(), fee_type="regular")


class TestSessionGroupExclusivity:
    """``enforce_session_group_exclusivity`` rejects two sessions in the same group."""

    def test_selecting_one_session_in_group_succeeds(self, grouped_event):
        tour_a = grouped_session(grouped_event, group="castle", title="Guided castle")
        registration = make_registration(grouped_event)

        registration.sessions.add(tour_a)

        assert tour_a in registration.sessions.all()

    def test_selecting_two_sessions_in_same_group_raises(self, grouped_event):
        tour_a = grouped_session(grouped_event, group="castle", title="Guided castle")
        tour_b = grouped_session(grouped_event, group="castle", title="Audio-guide castle")
        registration = make_registration(grouped_event)
        registration.sessions.add(tour_a)

        with pytest.raises(ValueError, match="conflicts with another selection in group 'castle'"):
            registration.sessions.add(tour_b)

    def test_switching_within_group_via_full_replace_succeeds(self, grouped_event):
        tour_a = grouped_session(grouped_event, group="castle", title="Guided castle")
        tour_b = grouped_session(grouped_event, group="castle", title="Audio-guide castle")
        registration = make_registration(grouped_event)
        registration.sessions.add(tour_a)

        # The frontend sends the full new selection set; the M2M diff means
        # pre_remove fires before pre_add, so the switch is conflict-free.
        registration.sessions.remove(tour_a)
        registration.sessions.add(tour_b)

        assert tour_b in registration.sessions.all()
        assert tour_a not in registration.sessions.all()

    def test_sessions_in_different_groups_allowed(self, grouped_event):
        castle = grouped_session(grouped_event, group="castle", title="Castle")
        boat = grouped_session(grouped_event, group="boat", title="Boat")
        registration = make_registration(grouped_event)

        registration.sessions.add(castle)
        registration.sessions.add(boat)

        assert set(registration.sessions.all()) == {castle, boat}

    def test_sessions_without_group_unaffected(self, grouped_event):
        tour_a = grouped_session(grouped_event, group="castle", title="Castle A")
        free_pick = SessionFactory(event=grouped_event, is_social_event=True, max_attendees=0, extra_data={})
        registration = make_registration(grouped_event)

        registration.sessions.add(tour_a)
        registration.sessions.add(free_pick)

        assert set(registration.sessions.all()) == {tour_a, free_pick}

    def test_empty_group_string_treated_as_no_group(self, grouped_event):
        empty_group_a = grouped_session(grouped_event, group="", title="Empty A")
        empty_group_b = grouped_session(grouped_event, group="   ", title="Empty B")
        registration = make_registration(grouped_event)

        # Both normalize to None, so no exclusivity is enforced.
        registration.sessions.add(empty_group_a)
        registration.sessions.add(empty_group_b)

        assert set(registration.sessions.all()) == {empty_group_a, empty_group_b}

    def test_readding_same_session_in_group_keeps_slot(self, grouped_event):
        tour_a = grouped_session(grouped_event, group="castle", title="Castle")
        registration = make_registration(grouped_event)
        registration.sessions.add(tour_a)

        # Re-adding the same session must not be blocked by its own group.
        registration.sessions.add(tour_a)
        assert tour_a in registration.sessions.all()


class TestSessionGroupAndCapacityInteraction:
    """Capacity enforcement and group exclusivity compose independently."""

    def test_capacity_error_takes_precedence_over_group(self, grouped_event):
        full_tour = grouped_session(grouped_event, group="castle", title="Castle A", max_attendees=1)
        first = make_registration(grouped_event)
        first.sessions.add(full_tour)

        second = make_registration(grouped_event)
        # The full session is at capacity before the group check matters.
        with pytest.raises(ValueError, match="full"):
            second.sessions.add(full_tour)

    def test_different_group_sibling_selectable_after_full(self, grouped_event):
        full_tour = grouped_session(grouped_event, group="castle", title="Castle A", max_attendees=1)
        other_tour = grouped_session(grouped_event, group="castle", title="Castle B")
        first = make_registration(grouped_event)
        first.sessions.add(full_tour)

        # A fresh registrant can select a different sibling in the same group.
        third = make_registration(grouped_event)
        third.sessions.add(other_tour)
        assert other_tour in third.sessions.all()
