"""Tests for per-fee-type registration caps (``Fee.config["max_registrations"]``).

A capped fee type refuses new registrations once the cap is reached. Re-saving
an existing registration (e.g. changing another field) must not be blocked by
its own slot. Rejected registrations do not count toward the cap.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from evan.models import Fee
from tests._factories import EventFactory, RegistrationFactory, UserFactory


def dt(s: str) -> datetime:
    """Parse an ISO-like datetime string into a UTC-aware datetime.

    :param s: A datetime string in ``YYYY-MM-DD HH:MM`` format.
    :returns: A timezone-aware datetime in UTC.
    """
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


@pytest.fixture
def capped_event(db):
    """An event with a capped ``phd`` fee (max 2) and an uncapped ``full`` fee."""
    event = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-03-01 00:00").date(),
        registration_deadline=dt("2026-08-31 23:59"),
        registration_early_deadline=None,
        registration_onsite_deadline=None,
    )
    Fee.objects.create(event=event, type="phd", value=0, config={"max_registrations": 2})
    Fee.objects.create(event=event, type="full", value=500)
    return event


class TestFeeCapEnforcement:
    """A capped fee type rejects registrations once the cap is reached."""

    def test_registration_allowed_below_cap(self, capped_event):
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

        assert reg.fee_type == "phd"
        assert reg.is_accepted is True

    def test_registration_blocked_at_cap(self, capped_event):
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

        with (
            pytest.raises(ValueError, match="sold out"),
            patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")),
        ):
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

    def test_uncapped_fee_type_unaffected_by_other_cap(self, capped_event):
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")
            full_reg = RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="full")

        assert full_reg.fee_type == "full"

    def test_resaving_existing_registration_keeps_its_slot(self, capped_event):
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")
            reg = RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

        # Cap is now reached; re-saving the same registration must not raise.
        reg.manual_extra_fees = 10
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg.save()

        reg.refresh_from_db()
        assert reg.manual_extra_fees == 10

    def test_changing_fee_type_into_sold_out_fee_is_blocked(self, capped_event):
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")
            RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")
            reg = RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="full")

        reg.fee_type = "phd"
        with (
            pytest.raises(ValueError, match="sold out"),
            patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")),
        ):
            reg.save()

    def test_rejected_registration_does_not_count_toward_cap(self, capped_event):
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            accepted = RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")
            rejected = RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

        rejected.is_accepted = False
        rejected.save()

        # Only `accepted` counts; one slot remains for a third PhD registration.
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            third = RegistrationFactory(event=capped_event, user=UserFactory(), fee_type="phd")

        assert third.is_accepted is True
        assert accepted.is_accepted is True


class TestFeeCapConfigValidation:
    """The fee config schema accepts and persists ``max_registrations``."""

    def test_max_registrations_persisted_in_config(self, db):
        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        fee = Fee.objects.create(event=event, type="phd", value=0, config={"max_registrations": 20})

        assert fee.config["max_registrations"] == 20

    def test_max_registrations_defaults_to_none_when_absent(self, db):
        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        fee = Fee.objects.create(event=event, type="full", value=500, config={})

        assert fee.config.get("max_registrations") is None


class TestFeeCapSerializerFields:
    """``FeeSerializer`` exposes ``is_sold_out`` and ``remaining_capacity``."""

    def test_uncapped_fee_reports_infinite_capacity(self, db):
        from evan.api.serializers import FeeSerializer

        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        fee = Fee.objects.create(event=event, type="full", value=500)

        data = FeeSerializer(fee).data
        assert data["is_sold_out"] is False
        assert data["remaining_capacity"] is None

    def test_capped_fee_reports_remaining_capacity(self, db):
        from evan.api.serializers import FeeSerializer

        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        fee = Fee.objects.create(event=event, type="phd", value=0, config={"max_registrations": 20})

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=event, user=UserFactory(), fee_type="phd")

        data = FeeSerializer(fee).data
        assert data["remaining_capacity"] == 19
        assert data["is_sold_out"] is False

    def test_capped_fee_sold_out_when_cap_reached(self, db):
        from evan.api.serializers import FeeSerializer

        event = EventFactory(
            start_date=dt("2026-09-01 00:00").date(),
            end_date=dt("2026-09-05 00:00").date(),
            registration_start_date=dt("2026-03-01 00:00").date(),
            registration_deadline=dt("2026-08-31 23:59"),
        )
        fee = Fee.objects.create(event=event, type="phd", value=0, config={"max_registrations": 1})

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=event, user=UserFactory(), fee_type="phd")

        data = FeeSerializer(fee).data
        assert data["remaining_capacity"] == 0
        assert data["is_sold_out"] is True
