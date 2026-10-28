"""Tests for registration model behavior: fee calculation, coupon discounts, and payment state.

We test the *outcomes* — what total is owed, what is paid, is the registration settled —
not the internal mechanics of individual calculation functions.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.db import IntegrityError

from evan.models import Coupon, Fee, RegistrationLog, RegistrationPaymentAttempt
from tests._factories import EventFactory, RegistrationFactory, SessionFactory, UserFactory


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
        with pytest.raises(IntegrityError), patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=event, user=user, fee_type="full")


# ---------------------------------------------------------------------------
# Accompanying-person fees (calculate_accompanying_fees)
# ---------------------------------------------------------------------------


@pytest.fixture
def event_with_socials(db):
    """An event with a flat fee and one social event carrying an extra_attendees_fee."""
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


class TestAccompanyingPersonFees:
    """Accompanying persons pay the session.extra_attendees_fee for each social event they select."""

    def test_two_persons_each_one_social_event(self, db, event_with_socials) -> None:
        social = SessionFactory(event=event_with_socials, is_social_event=True, extra_attendees_fee=20)

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(
                event=event_with_socials,
                user=UserFactory(),
                fee_type="full",
                extra_data={
                    "accompanying_persons": [
                        {"selected_social_events": [social.id]},
                        {"selected_social_events": [social.id]},
                    ]
                },
            )

        assert reg.extra_fees == 40
        assert reg.total_fee == 540

    def test_person_selecting_no_social_events_contributes_zero(self, db, event_with_socials) -> None:
        SessionFactory(event=event_with_socials, is_social_event=True, extra_attendees_fee=20)

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(
                event=event_with_socials,
                user=UserFactory(),
                fee_type="full",
                extra_data={"accompanying_persons": [{"selected_social_events": []}]},
            )

        assert reg.extra_fees == 0

    def test_no_accompanying_persons_key_yields_zero_fees(self, db, event_with_socials) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(
                event=event_with_socials,
                user=UserFactory(),
                fee_type="full",
                extra_data={},
            )

        assert reg.extra_fees == 0


# ---------------------------------------------------------------------------
# Social-event fees (calculate_social_event_fees)
# ---------------------------------------------------------------------------


class TestSocialEventFees:
    """When the selected social event is not included in the fee type, its extra_attendees_fee is added."""

    def test_included_social_event_charges_nothing(self, db, event_with_socials) -> None:
        social = SessionFactory(event=event_with_socials, is_social_event=True, extra_attendees_fee=20)
        Fee.objects.filter(event=event_with_socials, type="full").update(config={"included_social_events": [social.id]})

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event_with_socials, user=UserFactory(), fee_type="full")
        reg.sessions.add(social)
        reg.refresh_from_db()

        assert reg.base_fee == 500

    def test_non_included_social_event_adds_attendees_fee(self, db, event_with_socials) -> None:
        social = SessionFactory(event=event_with_socials, is_social_event=True, extra_attendees_fee=20)

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event_with_socials, user=UserFactory(), fee_type="full")
        reg.sessions.add(social)
        reg.refresh_from_db()

        assert reg.base_fee == 520


# ---------------------------------------------------------------------------
# Base-fee tiers (calculate_registration_base_fee)
# ---------------------------------------------------------------------------


@pytest.fixture
def tiered_event(db):
    """An event with early/regular/onsite tiers and the matching deadlines."""
    e = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-01-01 00:00").date(),
        registration_early_deadline=dt("2026-06-30 23:59"),
        registration_deadline=dt("2026-08-31 23:59"),
        registration_onsite_deadline=dt("2026-09-05 18:00"),
    )
    Fee.objects.create(event=e, type="full", early_value=300, value=500, onsite_value=700)
    return e


class TestRegistrationBaseFeeTiers:
    """The base fee reflects the pricing tier active when the registration was created."""

    def test_early_tier_uses_early_value(self, db, tiered_event) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-06-01 12:00")):
            reg = RegistrationFactory(event=tiered_event, user=UserFactory(), fee_type="full")

        assert reg.base_fee == 300

    def test_regular_tier_uses_value(self, db, tiered_event) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-15 12:00")):
            reg = RegistrationFactory(event=tiered_event, user=UserFactory(), fee_type="full")

        assert reg.base_fee == 500

    def test_onsite_tier_uses_onsite_value(self, db, tiered_event) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-09-02 10:00")):
            reg = RegistrationFactory(event=tiered_event, user=UserFactory(), fee_type="full")

        assert reg.base_fee == 700

    def test_onsite_value_none_falls_back_to_value(self, db, tiered_event) -> None:
        Fee.objects.filter(event=tiered_event, type="full").update(onsite_value=None)

        with patch("django.utils.timezone.now", return_value=dt("2026-09-02 10:00")):
            reg = RegistrationFactory(event=tiered_event, user=UserFactory(), fee_type="full")

        assert reg.base_fee == 500

    def test_early_value_none_falls_back_to_value(self, db, tiered_event) -> None:
        Fee.objects.filter(event=tiered_event, type="full").update(early_value=None)

        with patch("django.utils.timezone.now", return_value=dt("2026-06-01 12:00")):
            reg = RegistrationFactory(event=tiered_event, user=UserFactory(), fee_type="full")

        assert reg.base_fee == 500

    def test_missing_fee_type_raises_value_error(self, db, tiered_event) -> None:
        with (
            pytest.raises(ValueError, match="not found"),
            patch("django.utils.timezone.now", return_value=dt("2026-06-01 12:00")),
        ):
            RegistrationFactory(event=tiered_event, user=UserFactory(), fee_type="nonexistent")


# ---------------------------------------------------------------------------
# unique_hash rotation
# ---------------------------------------------------------------------------


class TestUniqueHashRotation:
    """The unique_hash rotates whenever the remaining fee changes, but stays put otherwise."""

    def test_new_registration_gets_eight_char_hash(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        assert reg.unique_hash
        assert len(reg.unique_hash) == 8

    def test_hash_rotates_when_remaining_fee_changes(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")
        original_hash = reg.unique_hash

        reg.manual_extra_fees = 50
        reg.save()

        assert reg.unique_hash != original_hash

    def test_hash_unchanged_when_fee_does_not_change(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")
        original_hash = reg.unique_hash

        reg.visa_requested = True
        reg.save()

        assert reg.unique_hash == original_hash


# ---------------------------------------------------------------------------
# Payment-attempt obsolescence (_obsolete_stale_payment_attempts)
# ---------------------------------------------------------------------------


class TestStalePaymentAttemptObsolescence:
    """When the ORDERID changes, previously pending attempts are marked obsolete."""

    def test_old_pending_attempt_marked_obsolete_when_fee_changes(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")
        old_order_id = reg.get_current_payment_order_id()
        attempt = RegistrationPaymentAttempt.objects.create(
            registration=reg,
            order_id=old_order_id,
            expected_amount=reg.remaining_fee,
        )

        reg.manual_extra_fees = 50
        reg.save()

        attempt.refresh_from_db()
        assert attempt.status == RegistrationPaymentAttempt.OBSOLETE
        assert attempt.resolved_at is not None

    def test_current_pending_attempt_is_preserved(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")
        current_order_id = reg.get_current_payment_order_id()
        current_attempt = RegistrationPaymentAttempt.objects.create(
            registration=reg,
            order_id=current_order_id,
            expected_amount=reg.remaining_fee,
        )

        reg.visa_requested = True
        reg.save()

        current_attempt.refresh_from_db()
        assert current_attempt.status == RegistrationPaymentAttempt.PENDING

    def test_no_payment_order_id_when_registration_settled(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")

        reg.paid = 500
        reg.save()

        assert reg.remaining_fee == 0
        assert reg.get_current_payment_order_id() is None


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


class TestRegistrationPostSaveSignal:
    """registration_post_save schedules a creation email and refreshes the event's registration count."""

    @patch("evan.services.mailer.registrations.schedule_registration_email")
    def test_creation_email_scheduled_on_create(self, mock_schedule, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=event, user=user, fee_type="full")

        mock_schedule.assert_called_once()
        args, kwargs = mock_schedule.call_args
        assert kwargs.get("code") == "registration.created" or args[-1:] == ("registration.created",)

    @patch("evan.services.mailer.registrations.schedule_registration_email")
    def test_registrations_count_incremented_on_create(self, mock_schedule, db, event, user) -> None:
        assert event.registrations_count == 0

        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            RegistrationFactory(event=event, user=user, fee_type="full")

        event.refresh_from_db()
        assert event.registrations_count == 1

    @patch("evan.services.mailer.registrations.schedule_registration_email")
    def test_creation_email_not_scheduled_on_update(self, mock_schedule, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")
        mock_schedule.reset_mock()

        reg.visa_requested = True
        reg.save()

        mock_schedule.assert_not_called()


class TestRegistrationSessionsChangedSignal:
    """registration_sessions_changed logs each newly added session and recalculates the fee."""

    def test_adding_session_creates_registration_log(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")
        session = SessionFactory(event=event)

        reg.sessions.add(session)

        logs = RegistrationLog.objects.filter(registration=reg)
        assert logs.count() == 1
        assert logs.first().session_id == session.id

    def test_adding_same_session_again_does_not_duplicate_log(self, db, event, user) -> None:
        with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
            reg = RegistrationFactory(event=event, user=user, fee_type="full")
        session = SessionFactory(event=event)

        reg.sessions.add(session)
        reg.sessions.add(session)

        assert RegistrationLog.objects.filter(registration=reg).count() == 1
