"""Tests for registration model behavior: fee calculation, coupon discounts, and payment state.

We test the *outcomes* — what total is owed, what is paid, is the registration settled —
not the internal mechanics of individual calculation functions.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.db import IntegrityError

from evan.models import Coupon, Fee
from tests._factories import EventFactory, RegistrationFactory, UserFactory


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


def dt(s: str) -> datetime:
    """Parse an ISO-like datetime string into a UTC-aware datetime.

    :param s: A datetime string in ``YYYY-MM-DD HH:MM`` format.
    :returns: A timezone-aware datetime in UTC.
    """
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


@pytest.fixture
def event(db):
    """A simple event with a single flat fee (no tier pricing)."""
    e = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-03-01 00:00").date(),
        registration_deadline=dt("2026-08-31 23:59"),
        registration_early_deadline=None,
        registration_onsite_deadline=None,
    )
    Fee.objects.create(event=e, type="full", value=500)
    return e


@pytest.fixture
def user(db):
    """A regular attendee user."""
    return UserFactory()


@pytest.fixture
def registration(db, event, user):
    """An unpaid registration for the full fee."""
    with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
        return RegistrationFactory(event=event, user=user, fee_type="full")


# ---------------------------------------------------------------------------
# Fee composition
# ---------------------------------------------------------------------------


class TestRegistrationFeeComposition:
    """total_fee = base_fee + extra_fees + manual_extra_fees."""

    def test_new_registration_base_fee_matches_fee_value(self, registration) -> None:
        assert registration.base_fee == 500

    def test_manual_extra_fee_increases_total(self, registration) -> None:
        registration.manual_extra_fees = 50
        registration.save()

        assert registration.total_fee == 550

    def test_total_fee_is_sum_of_all_components(self, registration) -> None:
        registration.manual_extra_fees = 25
        registration.save()

        assert registration.total_fee == registration.base_fee + registration.extra_fees + 25


# ---------------------------------------------------------------------------
# Payment state (saldo / is_paid)
# ---------------------------------------------------------------------------


class TestRegistrationPaymentState:
    """Saldo reflects the outstanding balance; is_paid is True when the account is settled."""

    def test_new_registration_is_unpaid(self, registration) -> None:
        assert registration.is_paid is False

    def test_saldo_equals_negative_total_fee_when_unpaid(self, registration) -> None:
        assert registration.saldo == -registration.total_fee

    def test_partial_payment_leaves_negative_saldo(self, db, event, user) -> None:
        """After a partial payment is recorded, the registration is still unpaid."""
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        # Simulate a payment recorded by the payment service
        reg.paid = 200
        reg.save()

        assert reg.saldo == -(500 - 200)
        assert reg.is_paid is False

    def test_full_payment_settles_the_registration(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        reg.paid = 500
        reg.save()

        assert reg.saldo == 0
        assert reg.is_paid is True

    def test_invoice_payment_settles_the_registration(self, db, event, user) -> None:
        """An invoice payment is as good as a direct payment for the saldo."""
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        reg.paid_via_invoice = 500
        reg.save()

        assert reg.is_paid is True


# ---------------------------------------------------------------------------
# Coupon discounts
# ---------------------------------------------------------------------------


class TestCouponDiscount:
    """Coupons reduce the outstanding balance through paid_via_coupon."""

    def test_base_fee_coupon_discounts_only_base_fee(self, db, event, user) -> None:
        """A BASE_FEE coupon is capped at the base_fee, not the total."""
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        coupon = Coupon.objects.create(event=event, value=200, coverage=Coupon.BASE_FEE)
        reg.coupon = coupon
        reg.save()

        assert reg.paid_via_coupon == 200
        assert reg.remaining_fee == 300

    def test_all_fees_coupon_discounts_total_fee(self, db, event, user) -> None:
        """An ALL_FEES coupon applies to the full total_fee."""
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        reg.manual_extra_fees = 100
        reg.save()

        coupon = Coupon.objects.create(event=event, value=200, coverage=Coupon.ALL_FEES)
        reg.coupon = coupon
        reg.save()

        # total_fee = 500 + 100 = 600; coupon covers 200 of that
        assert reg.paid_via_coupon == 200
        assert reg.remaining_fee == 400

    def test_coupon_exceeding_base_fee_is_capped(self, db, event, user) -> None:
        """A coupon larger than the base_fee only discounts up to the base_fee."""
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        coupon = Coupon.objects.create(event=event, value=999, coverage=Coupon.BASE_FEE)
        reg.coupon = coupon
        reg.save()

        assert reg.paid_via_coupon == 500  # capped at base_fee, not coupon value

    def test_full_coverage_coupon_fully_settles_registration(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        coupon = Coupon.objects.create(event=event, value=500, coverage=Coupon.ALL_FEES)
        reg.coupon = coupon
        reg.save()

        assert reg.is_paid is True
        assert reg.remaining_fee == 0


# ---------------------------------------------------------------------------
# Uniqueness
# ---------------------------------------------------------------------------


class TestRegistrationUniqueness:
    """Each user may only register once per event."""

    def test_duplicate_registration_raises_integrity_error(self, db, event, user, registration) -> None:
        """Attempting a second registration for the same (event, user) pair raises IntegrityError."""
        with pytest.raises(IntegrityError):
            with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
                RegistrationFactory(event=event, user=user, fee_type="full")
