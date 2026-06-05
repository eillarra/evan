"""Regression tests for the Ingenico payment result flow."""

from unittest.mock import patch

import pytest
from django.http import QueryDict

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
