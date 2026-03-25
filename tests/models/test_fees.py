"""Tests for fee pricing tier behavior and registration base fee calculation."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from evan.models import Fee
from tests._factories import EventFactory, RegistrationFactory, UserFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def dt(s: str) -> datetime:
    """Parse an ISO-like datetime string into a UTC-aware datetime.

    :param s: A datetime string in ``YYYY-MM-DD HH:MM`` format.
    :returns: A timezone-aware datetime in UTC.
    """
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def three_tier_event(db):
    """An event with early, late, and on-site registration periods.

    Periods:
    - Early:   until 2026-06-29 23:59
    - Late:    2026-06-30 → 2026-08-31 23:59
    - On-site: 2026-09-01 → 2026-09-05 18:00 (during the event)
    """
    event = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-03-01 00:00").date(),
        registration_early_deadline=dt("2026-06-29 23:59"),
        registration_deadline=dt("2026-08-31 23:59"),
        registration_onsite_deadline=dt("2026-09-05 18:00"),
    )
    Fee.objects.create(
        event=event,
        type="full",
        early_value=920,
        value=1170,
        onsite_value=1350,
    )
    Fee.objects.create(
        event=event,
        type="student",
        early_value=500,
        value=600,
        onsite_value=700,
    )
    return event


@pytest.fixture
def two_tier_event(db):
    """An event with only early and late periods — no on-site pricing."""
    event = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-03-01 00:00").date(),
        registration_early_deadline=dt("2026-06-29 23:59"),
        registration_deadline=dt("2026-08-31 23:59"),
        registration_onsite_deadline=None,
    )
    Fee.objects.create(event=event, type="full", early_value=920, value=1170, onsite_value=None)
    return event


@pytest.fixture
def flat_fee_event(db):
    """An event with a single flat fee — no date-based tiers at all."""
    event = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-03-01 00:00").date(),
        registration_early_deadline=None,
        registration_deadline=dt("2026-08-31 23:59"),
        registration_onsite_deadline=None,
    )
    Fee.objects.create(event=event, type="full", early_value=None, value=500, onsite_value=None)
    return event


@pytest.fixture
def t_user(db):
    """A regular attendee user."""
    return UserFactory()


# ---------------------------------------------------------------------------
# Three-tier fee resolution
# ---------------------------------------------------------------------------


class TestThreeTierFeeResolution:
    """Registrations created in each period map to the correct price."""

    def test_registration_in_early_period_uses_early_value(self, three_tier_event, t_user):
        with patch("django.utils.timezone.now", return_value=dt("2026-05-01 12:00")):
            reg = RegistrationFactory(event=three_tier_event, user=t_user, fee_type="full")

        assert reg.base_fee == 920

    def test_registration_in_late_period_uses_regular_value(self, three_tier_event, t_user):
        with patch("django.utils.timezone.now", return_value=dt("2026-07-15 12:00")):
            reg = RegistrationFactory(event=three_tier_event, user=t_user, fee_type="full")

        assert reg.base_fee == 1170

    def test_registration_in_onsite_period_uses_onsite_value(self, three_tier_event, t_user):
        with patch("django.utils.timezone.now", return_value=dt("2026-09-02 10:00")):
            reg = RegistrationFactory(event=three_tier_event, user=t_user, fee_type="full")

        assert reg.base_fee == 1350

    def test_student_fee_resolves_independently_per_tier(self, three_tier_event, t_user):
        with patch("django.utils.timezone.now", return_value=dt("2026-05-01 12:00")):
            reg = RegistrationFactory(event=three_tier_event, user=t_user, fee_type="student")

        assert reg.base_fee == 500

    def test_boundary_at_early_deadline_is_still_early(self, three_tier_event, t_user):
        with patch("django.utils.timezone.now", return_value=dt("2026-06-29 23:59")):
            reg = RegistrationFactory(event=three_tier_event, user=t_user, fee_type="full")

        assert reg.base_fee == 920

    def test_one_minute_after_early_deadline_is_late(self, three_tier_event, t_user):
        with patch("django.utils.timezone.now", return_value=dt("2026-06-30 00:00")):
            reg = RegistrationFactory(event=three_tier_event, user=t_user, fee_type="full")

        assert reg.base_fee == 1170

    def test_boundary_at_onsite_start_is_onsite(self, three_tier_event, t_user):
        # The first moment after the late registration deadline falls into on-site
        with patch("django.utils.timezone.now", return_value=dt("2026-09-01 00:00")):
            reg = RegistrationFactory(event=three_tier_event, user=t_user, fee_type="full")

        assert reg.base_fee == 1350


# ---------------------------------------------------------------------------
# Tier fallbacks when optional price values are not set
# ---------------------------------------------------------------------------


class TestTierFallbacks:
    """Missing tier values fall back gracefully to the regular price."""

    def test_missing_early_value_falls_back_to_regular_value(self, db, t_user):
        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_early_deadline=dt("2026-06-29 23:59"),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        Fee.objects.create(event=event, type="full", early_value=None, value=500)

        with patch("django.utils.timezone.now", return_value=dt("2026-05-01 12:00")):
            reg = RegistrationFactory(event=event, user=t_user, fee_type="full")

        assert reg.base_fee == 500

    def test_missing_onsite_value_falls_back_to_regular_value(self, db, t_user):
        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_early_deadline=dt("2026-06-29 23:59"),
            registration_deadline=dt("2026-08-31 23:59"),
            registration_onsite_deadline=dt("2026-09-05 18:00"),
        )
        Fee.objects.create(event=event, type="full", early_value=920, value=1170, onsite_value=None)

        with patch("django.utils.timezone.now", return_value=dt("2026-09-02 10:00")):
            reg = RegistrationFactory(event=event, user=t_user, fee_type="full")

        assert reg.base_fee == 1170

    def test_no_early_deadline_always_charges_regular_value(self, flat_fee_event, t_user):
        with patch("django.utils.timezone.now", return_value=dt("2026-03-15 12:00")):
            reg = RegistrationFactory(event=flat_fee_event, user=t_user, fee_type="full")

        assert reg.base_fee == 500

    def test_no_onsite_deadline_never_triggers_onsite_pricing(self, two_tier_event, t_user):
        # After registration_deadline there is no on-site window → still regular value
        with patch("django.utils.timezone.now", return_value=dt("2026-09-02 10:00")):
            # Event is past the deadline but no onsite window → is_open_for_registration=False here,
            # but `event.is_onsite` should return False and fee should use regular value
            reg = RegistrationFactory(event=two_tier_event, user=t_user, fee_type="full")

        assert reg.base_fee == 1170


# ---------------------------------------------------------------------------
# Social event extras included vs. charged
# ---------------------------------------------------------------------------


class TestSocialEventFeeInclusion:
    """Fees that include specific social events do not charge extra for them."""

    def test_social_event_included_in_fee_has_no_extra_charge(self, db, t_user):
        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        from evan.models import Session

        social = Session.objects.create(
            event=event,
            title="Gala Dinner",
            is_social_event=True,
            extra_attendees_fee=75,
        )
        fee = Fee.objects.create(
            event=event,
            type="full",
            value=1170,
            config={"included_social_events": [social.id]},
        )

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=t_user, fee_type="full")
            reg.sessions.add(social)
            reg.save()

        assert reg.base_fee == 1170
        assert reg.extra_fees == 0

    def test_social_event_not_included_in_fee_is_charged_as_extra(self, db, t_user):
        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        from evan.models import Session

        social = Session.objects.create(
            event=event,
            title="Monday Reception",
            is_social_event=True,
            extra_attendees_fee=25,
        )
        Fee.objects.create(event=event, type="full", value=770, config={"included_social_events": []})

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=t_user, fee_type="full")
            reg.sessions.add(social)
            reg.save()

        assert reg.base_fee == 795
        assert reg.extra_fees == 0
        assert reg.total_fee == 795
