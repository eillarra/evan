from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils.timezone import now

from evan.models import Fee, RegistrationPaymentAttempt
from evan.tasks.payments import alert_on_stale_payment_attempts
from tests._factories import EventFactory, RegistrationFactory, UserFactory


def _registration_with_fee():
    event = EventFactory()
    Fee.objects.create(event=event, type="regular", value=100)
    return RegistrationFactory(event=event, user=UserFactory())


@pytest.fixture
def stale_pending_attempt(db) -> RegistrationPaymentAttempt:
    """A payment attempt that has been PENDING well beyond a normal payment session."""
    registration = _registration_with_fee()
    attempt = RegistrationPaymentAttempt.objects.create(
        registration=registration,
        order_id=f"{registration.pk}-stale",
        expected_amount=100,
    )
    RegistrationPaymentAttempt.objects.filter(pk=attempt.pk).update(created_at=now() - timedelta(hours=3))
    return attempt


@pytest.mark.django_db
class TestAlertOnStalePaymentAttempts:
    @patch("evan.tasks.payments.sentry_sdk.capture_message")
    def test_stale_pending_attempt_triggers_alert(self, mock_capture, stale_pending_attempt) -> None:
        alert_on_stale_payment_attempts()

        mock_capture.assert_called_once()
        assert str(stale_pending_attempt.registration_id) in mock_capture.call_args.args[0]

    @patch("evan.tasks.payments.sentry_sdk.capture_message")
    def test_stale_attempt_diagnostic_distinguishes_no_callback_from_exception(self, mock_capture, db) -> None:
        """Alert extra data must flag whether each stuck attempt ever received a callback.

        Two stale attempts: one with no callback at all (the gap b3d9231 cannot
        close), one with an EXCEPTION status callback (the gap intentionally
        left for admin). Both surface in the same alert, but the per-attempt
        diagnostic must let Sentry tell them apart without a manual DB dig.
        """
        no_callback_registration = _registration_with_fee()
        no_callback_attempt = RegistrationPaymentAttempt.objects.create(
            registration=no_callback_registration,
            order_id=f"{no_callback_registration.pk}-no-cb",
            expected_amount=100,
        )
        exception_registration = _registration_with_fee()
        exception_attempt = RegistrationPaymentAttempt.objects.create(
            registration=exception_registration,
            order_id=f"{exception_registration.pk}-exc",
            expected_amount=100,
            callback_data={"STATUS": "52", "PAYID": "999"},
        )
        RegistrationPaymentAttempt.objects.filter(pk__in=[no_callback_attempt.pk, exception_attempt.pk]).update(
            created_at=now() - timedelta(hours=3)
        )

        alert_on_stale_payment_attempts()

        extra = mock_capture.call_args.kwargs["extra"]["stale_attempts"]
        by_order = {entry["order_id"]: entry for entry in extra}
        assert by_order[no_callback_attempt.order_id]["callback_received"] is False
        assert by_order[no_callback_attempt.order_id]["last_status"] is None
        assert by_order[exception_attempt.order_id]["callback_received"] is True
        assert by_order[exception_attempt.order_id]["last_status"] == "52"

    @patch("evan.tasks.payments.sentry_sdk.capture_message")
    def test_fresh_pending_attempt_does_not_trigger_alert(self, mock_capture, db) -> None:
        registration = _registration_with_fee()
        RegistrationPaymentAttempt.objects.create(
            registration=registration,
            order_id=f"{registration.pk}-fresh",
            expected_amount=100,
        )

        alert_on_stale_payment_attempts()

        mock_capture.assert_not_called()

    @patch("evan.tasks.payments.sentry_sdk.capture_message")
    def test_resolved_attempt_does_not_trigger_alert(self, mock_capture, stale_pending_attempt) -> None:
        stale_pending_attempt.mark_resolved(status=RegistrationPaymentAttempt.SUCCEEDED, payid="1234567890")
        stale_pending_attempt.save()

        alert_on_stale_payment_attempts()

        mock_capture.assert_not_called()
