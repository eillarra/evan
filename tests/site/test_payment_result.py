"""Regression tests for the Ingenico payment result flow."""

from unittest.mock import patch

import pytest
from django.http import QueryDict
from django.urls import reverse

from evan.models import Fee
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


@pytest.mark.django_db
class TestCreditIngenicoPayment:
    """Boundary tests for the _credit_ingenico_payment helper."""

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_decimal_amount_string_is_credited_correctly(self, _mock_validate, payment_registration) -> None:
        """Ogone returns AMOUNT as a decimal string; must not raise ValueError."""
        qs = QueryDict("PAYID=5451031176&AMOUNT=795.00&STATUS=9")

        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is True
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 795
        assert payment_registration.payid == "5451031176"

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_integer_amount_string_is_still_credited_correctly(self, _mock_validate, payment_registration) -> None:
        """Integer-formatted AMOUNT strings must continue to work after the fix."""
        qs = QueryDict("PAYID=1234567890&AMOUNT=920&STATUS=9")

        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is True
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 920

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_duplicate_payid_is_rejected(self, _mock_validate, payment_registration) -> None:
        """A second callback with the same PAYID must not double-credit the registration."""
        payment_registration.payid = "5451031176"
        payment_registration.paid = 795
        payment_registration.save()

        qs = QueryDict("PAYID=5451031176&AMOUNT=795.00&STATUS=9")
        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 795

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=False)
    def test_invalid_signature_is_rejected(self, _mock_validate, payment_registration) -> None:
        """Tampered query parameters must not credit the registration."""
        qs = QueryDict("PAYID=9999999999&AMOUNT=795.00&STATUS=9")
        result = _credit_ingenico_payment(payment_registration, qs)

        assert result is False
        payment_registration.refresh_from_db()
        assert payment_registration.paid == 0

    @patch("evan.site.views.registrations.Ingenico.validate_out_parameters", return_value=True)
    def test_unique_hash_is_rotated_after_successful_payment(self, _mock_validate, payment_registration) -> None:
        """After a successful payment the unique_hash must change so any future
        payment attempt gets a fresh ORDERID and Ingenico does not reject it."""
        original_hash = payment_registration.unique_hash
        qs = QueryDict("PAYID=1111111111&AMOUNT=100.00&STATUS=9")

        _credit_ingenico_payment(payment_registration, qs)

        payment_registration.refresh_from_db()
        assert payment_registration.unique_hash != original_hash
        assert len(payment_registration.unique_hash) == 8


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
