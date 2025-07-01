"""Tests for RegistrationAdmin actions."""

from unittest.mock import Mock

import pytest
from django.contrib.admin import site
from django.http import HttpResponse

from evan.admin.registrations import RegistrationAdmin
from evan.models import Registration
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
