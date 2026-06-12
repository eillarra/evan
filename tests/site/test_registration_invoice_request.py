"""Tests for registration invoice request flow behavior."""

from http import HTTPStatus as status
from unittest.mock import patch

import pytest
from django.urls import reverse

from evan.models import Fee
from tests._factories import EventFactory, RegistrationFactory, UserFactory


def _invoice_request_url(registration) -> str:
    """Build the invoice request URL for a registration."""
    return reverse("registration:invoice_request", args=[registration.uuid])


@pytest.fixture
def invoice_ready_registration(db):
    """Create an accepted unpaid registration for an event allowing invoices."""
    event = EventFactory()
    event.config = {
        "payments": {
            "type": "ugent",
            "wbs_element": "TESTPSP",
            "ingenico_salt": "testsalt",
            "allow_invoices": True,
        }
    }
    event.save()
    Fee.objects.create(event=event, type="regular", value=100)

    user = UserFactory()
    return RegistrationFactory(event=event, user=user, fee_type="regular", is_accepted=True)


@pytest.mark.site
@pytest.mark.django_db
class TestRegistrationInvoiceRequestView:
    """Boundary tests for invoice requests from the site flow."""

    @patch("evan.site.views.registrations.schedule_registration_email")
    def test_first_request_marks_flag_and_sends_email_once(
        self, mocked_schedule_email, client, invoice_ready_registration
    ):
        """First invoice request marks invoice_requested and sends one reminder email."""
        client.force_login(invoice_ready_registration.user)

        response = client.get(_invoice_request_url(invoice_ready_registration))

        assert response.status_code == status.FOUND
        invoice_ready_registration.refresh_from_db()
        assert invoice_ready_registration.invoice_requested is True
        mocked_schedule_email.assert_called_once_with(invoice_ready_registration, code="registration.payment_reminder")

    @patch("evan.site.views.registrations.schedule_registration_email")
    def test_second_request_is_idempotent_and_does_not_send_email_again(
        self, mocked_schedule_email, client, invoice_ready_registration
    ):
        """Repeated invoice requests do not re-send email once already requested."""
        client.force_login(invoice_ready_registration.user)

        response1 = client.get(_invoice_request_url(invoice_ready_registration))
        response2 = client.get(_invoice_request_url(invoice_ready_registration))

        assert response1.status_code == status.FOUND
        assert response2.status_code == status.FOUND
        invoice_ready_registration.refresh_from_db()
        assert invoice_ready_registration.invoice_requested is True
        mocked_schedule_email.assert_called_once_with(invoice_ready_registration, code="registration.payment_reminder")

    @patch("evan.site.views.registrations.schedule_registration_email")
    def test_paid_registration_does_not_mark_invoice_requested(
        self, mocked_schedule_email, client, invoice_ready_registration
    ):
        """Already paid registrations cannot switch to invoice flow."""
        invoice_ready_registration.paid = invoice_ready_registration.total_fee
        invoice_ready_registration.save()
        client.force_login(invoice_ready_registration.user)

        response = client.get(_invoice_request_url(invoice_ready_registration))

        assert response.status_code == status.FOUND
        invoice_ready_registration.refresh_from_db()
        assert invoice_ready_registration.invoice_requested is False
        mocked_schedule_email.assert_not_called()

    @patch("evan.site.views.registrations.schedule_registration_email")
    def test_unaccepted_registration_is_forbidden(self, mocked_schedule_email, client, invoice_ready_registration):
        """Unaccepted registrations cannot request invoices."""
        invoice_ready_registration.is_accepted = False
        invoice_ready_registration.save()
        client.force_login(invoice_ready_registration.user)

        response = client.get(_invoice_request_url(invoice_ready_registration))

        assert response.status_code == status.FORBIDDEN
        invoice_ready_registration.refresh_from_db()
        assert invoice_ready_registration.invoice_requested is False
        mocked_schedule_email.assert_not_called()

    @patch("evan.site.views.registrations.schedule_registration_email")
    def test_disallowed_event_invoices_are_forbidden(self, mocked_schedule_email, client, invoice_ready_registration):
        """Events configured without invoices reject invoice requests."""
        event = invoice_ready_registration.event
        event.config = {
            "payments": {
                "type": "ugent",
                "wbs_element": "TESTPSP",
                "ingenico_salt": "testsalt",
                "allow_invoices": False,
            }
        }
        event.save()
        client.force_login(invoice_ready_registration.user)

        response = client.get(_invoice_request_url(invoice_ready_registration))

        assert response.status_code == status.FORBIDDEN
        invoice_ready_registration.refresh_from_db()
        assert invoice_ready_registration.invoice_requested is False
        mocked_schedule_email.assert_not_called()
