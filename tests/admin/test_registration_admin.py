"""Tests for RegistrationAdmin actions."""

from unittest.mock import Mock

import pytest
from django.contrib.admin import site
from django.http import HttpResponse
from django.urls import reverse

from evan.admin.registrations import RegistrationAdmin
from evan.models import InvitationLetter, Registration
from tests._factories import EventFactory, UserFactory


@pytest.mark.django_db
class TestRegistrationAdminActions:
    """Test the RegistrationAdmin custom actions."""

    def test_view_badges_pdf_action_exists(self, rf, t_superuser):
        """Test that the view_badges_pdf action is available."""
        admin_instance = RegistrationAdmin(Registration, site)
        request = rf.get("/admin/")
        request.user = t_superuser

        actions = admin_instance.get_actions(request)
        action_names = list(actions.keys())

        assert "view_badges_pdf" in action_names

    def test_view_badges_pdf_no_accepted_registrations(self, rf, t_event, t_event_manager, t_superuser):
        """Test view_badges_pdf with no accepted registrations."""
        user = UserFactory()

        # Ensure the event doesn't auto-accept registrations
        t_event.accept_by_default = False
        t_event.save()

        # Create a registration that is not accepted
        registration = Registration.objects.create(event=t_event, user=user, is_accepted=False, fee_type="regular")

        # Force update to ensure is_accepted is False after save
        registration.is_accepted = False
        registration.save()

        # Verify the registration is actually not accepted
        registration.refresh_from_db()
        assert not registration.is_accepted

        admin_instance = RegistrationAdmin(Registration, site)
        request = rf.post("/admin/")
        request.user = t_superuser
        queryset = Registration.objects.filter(pk=registration.pk)

        # Mock the message_user method to capture messages
        admin_instance.message_user = Mock()

        response = admin_instance.view_badges_pdf(request, queryset)

        # Should return None and show warning message
        assert response is None
        admin_instance.message_user.assert_called_once_with(
            request, "No accepted registrations selected.", level="warning"
        )

    def test_view_badges_pdf_multiple_events(self, rf, t_superuser):
        """Test view_badges_pdf with registrations from different events."""
        user = UserFactory()

        # Create two events with fees
        event1 = EventFactory(name="Event 1", code="event1")
        event2 = EventFactory(name="Event 2", code="event2")

        # Create fees for both events
        from evan.models import Fee

        Fee.objects.create(event=event1, type="regular", value=100)
        Fee.objects.create(event=event2, type="regular", value=100)

        # Create registrations for different events
        reg1 = Registration.objects.create(event=event1, user=user, is_accepted=True, fee_type="regular")
        reg2 = Registration.objects.create(event=event2, user=user, is_accepted=True, fee_type="regular")

        admin_instance = RegistrationAdmin(Registration, site)
        request = rf.post("/admin/")
        request.user = t_superuser
        queryset = Registration.objects.filter(pk__in=[reg1.pk, reg2.pk])

        # Mock the message_user method
        admin_instance.message_user = Mock()

        response = admin_instance.view_badges_pdf(request, queryset)

        # Should return None and show error message
        assert response is None
        admin_instance.message_user.assert_called_once()
        call_args = admin_instance.message_user.call_args
        assert "Cannot generate badges for registrations from different events" in call_args[0][1]
        assert call_args[1]["level"] == "error"

    def test_view_badges_pdf_success(self, rf, t_event, t_event_manager, t_superuser):
        """Test view_badges_pdf with valid accepted registrations."""
        user = UserFactory()

        # Create accepted registrations
        registration = Registration.objects.create(event=t_event, user=user, is_accepted=True, fee_type="regular")

        admin_instance = RegistrationAdmin(Registration, site)
        request = rf.post("/admin/")
        request.user = t_superuser
        queryset = Registration.objects.filter(pk=registration.pk)

        response = admin_instance.view_badges_pdf(request, queryset)

        # Should return an HttpResponse (PDF)
        assert isinstance(response, HttpResponse)
        assert response["Content-Type"] == "application/pdf"

    def test_change_view_can_delete_invitation_letter_inline(self, client, t_event, t_superuser):
        """Deleting invitation letter inline should not crash in admin."""
        user = UserFactory()
        registration = Registration.objects.create(
            event=t_event,
            user=user,
            is_accepted=True,
            fee_type="regular",
        )
        invitation_letter = InvitationLetter.objects.create(
            registration=registration,
            name="John Doe",
            passport_number="ABC123",
            nationality="Belgian",
            address="Some address",
        )

        client.force_login(t_superuser)
        response = client.post(
            reverse("admin:evan_registration_change", args=[registration.pk]),
            {
                "event": str(registration.event_id),
                "user": str(registration.user_id),
                "is_accepted": "on",
                "fee_type": registration.fee_type,
                "manual_extra_fees": str(registration.manual_extra_fees),
                "paid_via_invoice": str(registration.paid_via_invoice),
                "invoice_requested": "on" if registration.invoice_requested else "",
                "invoice_sent": "on" if registration.invoice_sent else "",
                "coupon": "",
                "visa_requested": "on" if registration.visa_requested else "",
                "visa_sent": "on" if registration.visa_sent else "",
                "letter-TOTAL_FORMS": "1",
                "letter-INITIAL_FORMS": "1",
                "letter-MIN_NUM_FORMS": "0",
                "letter-MAX_NUM_FORMS": "1",
                "letter-0-registration": str(registration.pk),
                "letter-0-name": invitation_letter.name,
                "letter-0-passport_number": invitation_letter.passport_number,
                "letter-0-nationality": invitation_letter.nationality,
                "letter-0-address": invitation_letter.address,
                "letter-0-submitted": invitation_letter.submitted,
                "letter-0-submitted_title": invitation_letter.submitted_title,
                "letter-0-notes": invitation_letter.notes,
                "letter-0-DELETE": "on",
                "_save": "Save",
            },
            follow=True,
        )

        assert response.status_code == 200
        assert InvitationLetter.objects.filter(pk=registration.pk).exists() is False
