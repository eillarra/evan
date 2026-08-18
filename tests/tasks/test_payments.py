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
