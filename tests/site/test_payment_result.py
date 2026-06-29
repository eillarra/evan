"""Regression tests for the Ingenico payment result flow."""

from unittest.mock import patch

import pytest
from django.http import QueryDict
from django.urls import reverse

from evan.models import Fee, RegistrationPaymentAttempt
from evan.services.payments.ingenico import Ingenico
from evan.site.views.registrations import _credit_ingenico_payment
from tests._factories import EventFactory, RegistrationFactory, UserFactory


@pytest.fixture
def payment_registration(db):
    """An accepted registration wired to an event with Ingenico configuration."""
    event = EventFactory()
    # Set up Ingenico payment configuration via the underlying config JSONField.
    event.config = {"payments": {"type": "ugent", "wbs_element": "TESTPSP", "ingenico_salt": "testsalt"}}
    event.save()
    Fee.objects.create(event=event, type="regular", value=100)

    user = UserFactory()
    registration = RegistrationFactory(event=event, user=user)
    return registration


def create_pending_attempt(registration, *, amount: int | None = None) -> RegistrationPaymentAttempt:
    """Create the deterministic pending attempt used by the Ingenico form.

    :param registration: Registration under test.
    :param amount: Optional override amount.
    :returns: The persisted pending payment attempt.
    """
    expected_amount = registration.remaining_fee if amount is None else amount
    order_id = Ingenico.generate_order_id(registration.pk, expected_amount, registration.unique_hash)
    return RegistrationPaymentAttempt.objects.create(
        registration=registration,
        order_id=order_id,
        expected_amount=expected_amount,
    )


def callback_qs(
    attempt: RegistrationPaymentAttempt, *, payid: str, amount: int | None = None, status: str = "9"
) -> QueryDict:
    """Build a callback querystring for a stored attempt.

    :param attempt: The payment attempt to reference.
    :param payid: Ingenico payment identifier.
    :param amount: Optional override amount in EUR.
    :param status: Ingenico status code.
    :returns: A query dict matching the payment callback format.
    """
    expected_amount = attempt.expected_amount if amount is None else amount
    return QueryDict(f"PAYID={payid}&ORDERID={attempt.order_id}&AMOUNT={expected_amount:.2f}&STATUS={status}")


@pytest.mark.django_db
class TestCreditIngenicoPayment:
    """Boundary tests for the _credit_ingenico_payment helper."""

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_decimal_amount_string_is_credited_correctly(self, _mock_validate, payment_registration) -> None:
        """Ogone returns AMOUNT as a decimal string; must not raise ValueError."""
        attempt = create_pending_attempt(payment_registration, amount=795)
        qs = callback_qs(attempt, payid="5451031176")

        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is True
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 795
        assert payment_registration.payid == "5451031176"
        attempt.refresh_from_db()
        assert attempt.status == RegistrationPaymentAttempt.SUCCEEDED

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_integer_amount_string_is_still_credited_correctly(self, _mock_validate, payment_registration) -> None:
        """Integer-formatted AMOUNT strings must continue to work after the fix."""
        attempt = create_pending_attempt(payment_registration, amount=920)
        qs = QueryDict(f"PAYID=1234567890&ORDERID={attempt.order_id}&AMOUNT=920&STATUS=9")

        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is True
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 920

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_duplicate_payid_is_rejected(self, _mock_validate, payment_registration) -> None:
        """A second callback with the same PAYID must not double-credit the registration."""
        attempt = create_pending_attempt(payment_registration, amount=795)
        qs = callback_qs(attempt, payid="5451031176")

        first_result = _credit_ingenico_payment(payment_registration, qs)
        second_result = _credit_ingenico_payment(payment_registration, qs)

        assert first_result is True
        assert second_result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 795

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=False)
    def test_invalid_signature_is_rejected(self, _mock_validate, payment_registration) -> None:
        """Tampered query parameters must not credit the registration."""
        attempt = create_pending_attempt(payment_registration, amount=795)
        qs = callback_qs(attempt, payid="9999999999")
        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 0

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_unique_hash_is_rotated_after_successful_payment(self, _mock_validate, payment_registration) -> None:
        """After a successful payment the unique_hash must change so any future
        payment attempt gets a fresh ORDERID and Ingenico does not reject it."""
        original_hash = payment_registration.unique_hash
        attempt = create_pending_attempt(payment_registration, amount=100)
        qs = callback_qs(attempt, payid="1111111111")

        _credit_ingenico_payment(payment_registration, qs)

        payment_registration.refresh_from_db()
        assert payment_registration.unique_hash != original_hash
        assert len(payment_registration.unique_hash) == 8

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_replayed_callback_with_new_payid_is_rejected(self, _mock_validate, payment_registration) -> None:
        """A replayed callback for the same ORDERID must not re-credit with a new PAYID."""
        attempt = create_pending_attempt(payment_registration, amount=795)

        first_result = _credit_ingenico_payment(payment_registration, callback_qs(attempt, payid="5451031176"))
        second_result = _credit_ingenico_payment(payment_registration, callback_qs(attempt, payid="9999999999"))

        assert first_result is True
        assert second_result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 795

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_callback_without_matching_attempt_is_rejected(self, _mock_validate, payment_registration) -> None:
        """Only callbacks for stored payment attempts may credit a registration."""
        qs = QueryDict("PAYID=5451031176&ORDERID=missing-order-id&AMOUNT=795.00&STATUS=9")

        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 0


@pytest.mark.django_db
class TestPaymentFormAttempts:
    """Payment form rendering should persist a deterministic pending payment attempt."""

    def test_payment_page_creates_pending_attempt(self, client, payment_registration) -> None:
        client.force_login(payment_registration.user)

        response = client.get(reverse("registration:payment", args=[payment_registration.uuid]))

        assert response.status_code == 200
        attempts = RegistrationPaymentAttempt.objects.filter(registration=payment_registration)
        assert attempts.count() == 1
        attempt = attempts.get()
        assert attempt.status == RegistrationPaymentAttempt.PENDING
        assert attempt.expected_amount == payment_registration.remaining_fee

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_pending_attempt_is_obsoleted_when_amount_increases(self, _mock_validate, payment_registration) -> None:
        """Increasing the amount due must obsolete the previously pending payment attempt."""
        attempt = create_pending_attempt(payment_registration)
        old_hash = payment_registration.unique_hash

        payment_registration.manual_extra_fees = 40
        payment_registration.save()

        attempt.refresh_from_db()
        assert attempt.status == RegistrationPaymentAttempt.OBSOLETE
        assert payment_registration.unique_hash != old_hash
        assert payment_registration.remaining_fee == 140

        result = _credit_ingenico_payment(payment_registration, callback_qs(attempt, payid="stale-amount-up"))

        assert result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 0

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_pending_attempt_is_obsoleted_when_amount_decreases(self, _mock_validate, payment_registration) -> None:
        """Decreasing the amount due must obsolete the previously pending payment attempt."""
        payment_registration.manual_extra_fees = 40
        payment_registration.save()
        attempt = create_pending_attempt(payment_registration)
        old_hash = payment_registration.unique_hash

        payment_registration.manual_extra_fees = 0
        payment_registration.save()

        attempt.refresh_from_db()
        assert attempt.status == RegistrationPaymentAttempt.OBSOLETE
        assert payment_registration.unique_hash != old_hash
        assert payment_registration.remaining_fee == 100

        result = _credit_ingenico_payment(payment_registration, callback_qs(attempt, payid="stale-amount-down"))

        assert result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 0


@pytest.mark.django_db
class TestPaymentResultViewHashRotation:
    """Regression tests: unique_hash must be rotated on cancel and decline so
    the next payment attempt uses a fresh ORDERID.

    Background: Ingenico registers the ORDERID the moment the payment form is
    submitted.  If the user cancels (or the card is declined) and immediately
    tries again, Ingenico rejects the same ORDERID with 'This payment has
    already been processed.'
    """

    def _get_result_url(self, registration):
        return reverse("registration:payment_result", args=[registration.uuid])

    def test_hash_is_rotated_on_cancel(self, client, payment_registration) -> None:
        """STATUS=1 (cancel) must rotate unique_hash before redirecting."""
        original_hash = payment_registration.unique_hash

        client.get(self._get_result_url(payment_registration), {"STATUS": "1"})

        payment_registration.refresh_from_db()
        assert payment_registration.unique_hash != original_hash
        assert len(payment_registration.unique_hash) == 8

    def test_hash_is_rotated_on_decline(self, client, payment_registration) -> None:
        """STATUS=2 (decline) must rotate unique_hash before redirecting."""
        original_hash = payment_registration.unique_hash

        client.get(self._get_result_url(payment_registration), {"STATUS": "2"})

        payment_registration.refresh_from_db()
        assert payment_registration.unique_hash != original_hash
        assert len(payment_registration.unique_hash) == 8

    def test_hash_is_not_rotated_on_exception(self, client, payment_registration) -> None:
        """STATUS=52 (exception / under review) must NOT rotate the hash;
        admin must manually clear it after confirming the outcome with Ingenico."""
        original_hash = payment_registration.unique_hash

        client.get(self._get_result_url(payment_registration), {"STATUS": "52"})

        payment_registration.refresh_from_db()
        assert payment_registration.unique_hash == original_hash
