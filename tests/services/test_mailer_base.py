"""Tests for mailer base utilities."""

from unittest.mock import patch

import pytest
from django.test import override_settings

from evan.services.mailer.base import (
    get_template,
    render_context,
    schedule_email,
    schedule_template_email,
    send_email_to_admins,
)
from tests._factories import EmailTemplateFactory, EventFactory, UserFactory


@pytest.mark.django_db
class TestRenderContext:
    """Test the render_context function."""

    def test_render_context_simple(self):
        """Test rendering simple context."""
        body = "Hello {{ name }}!"
        context = {"name": "World"}
        result = render_context(body, context)
        assert result == "Hello World!"

    def test_render_context_multiple_variables(self):
        """Test rendering with multiple variables."""
        body = "Event: {{ event_name }} on {{ date }}"
        context = {"event_name": "Conference 2024", "date": "2024-01-15"}
        result = render_context(body, context)
        assert result == "Event: Conference 2024 on 2024-01-15"

    def test_render_context_empty_context(self):
        """Test rendering with empty context."""
        body = "Static text without variables"
        context = {}
        result = render_context(body, context)
        assert result == "Static text without variables"

    def test_render_context_missing_variable(self):
        """Test rendering with missing variable in context."""
        body = "Hello {{ missing_var }}!"
        context = {"other_var": "value"}
        result = render_context(body, context)
        assert result == "Hello !"


@pytest.mark.django_db
class TestGetTemplate:
    """Test the get_template function."""

    def test_get_template_event_specific(self):
        """Test getting event-specific template."""
        event = EventFactory()
        template = EmailTemplateFactory(event=event, code="welcome")

        result = get_template(event, "welcome")
        assert result == template

    def test_get_template_global_fallback(self):
        """Test falling back to global template when event-specific not found."""
        event = EventFactory()
        global_template = EmailTemplateFactory(event=None, code="welcome")

        result = get_template(event, "welcome")
        assert result == global_template

    @patch("evan.services.mailer.base.send_email_to_admins")
    def test_get_template_not_found(self, mock_send_email):
        """Test error when template is not found."""
        event = EventFactory()

        with pytest.raises(ValueError, match="Email template not found"):
            get_template(event, "nonexistent")

        mock_send_email.assert_called_once()

    def test_get_template_default_language(self):
        """Test that get_template works without language parameter."""
        event = EventFactory()
        template = EmailTemplateFactory(event=event, code="welcome")

        result = get_template(event, "welcome")  # No language needed
        assert result == template


class TestSendEmailToAdmins:
    """Test the send_email_to_admins function."""

    @patch("evan.services.mailer.base.django_send_mail")
    @override_settings(ADMINS=[("Admin", "admin@example.com")])
    def test_send_email_to_admins_basic(self, mock_send_mail):
        """Test sending basic email to admins."""
        send_email_to_admins("Test Subject", "Test Message")

        mock_send_mail.assert_called_once_with(
            "[evan] Test Subject",
            "Test Message",
            "UGent <evan@ugent.be>",
            [("Admin", "admin@example.com")],
            fail_silently=False,
        )

    @patch("evan.services.mailer.base.django_send_mail")
    @override_settings(ADMINS=[("Admin", "admin@example.com")])
    def test_send_email_to_admins_with_evan_prefix(self, mock_send_mail):
        """Test that [evan] prefix is not duplicated."""
        send_email_to_admins("[evan] Already Prefixed", "Test Message")

        mock_send_mail.assert_called_once_with(
            "[evan] Already Prefixed",
            "Test Message",
            "UGent <evan@ugent.be>",
            [("Admin", "admin@example.com")],
            fail_silently=False,
        )

    @patch("evan.services.mailer.base.django_send_mail")
    @override_settings(ADMINS=[("Admin", "admin@example.com")])
    def test_send_email_to_admins_empty_message(self, mock_send_mail):
        """Test sending email with empty message."""
        send_email_to_admins("Test Subject")

        mock_send_mail.assert_called_once_with(
            "[evan] Test Subject",
            "",
            "UGent <evan@ugent.be>",
            [("Admin", "admin@example.com")],
            fail_silently=False,
        )


@pytest.mark.django_db
class TestScheduleEmail:
    """Test the schedule_email function."""

    @patch("evan.models.emails.EmailLog.objects.create")
    def test_schedule_email_basic(self, mock_create):
        """Test scheduling basic email."""
        schedule_email(to=["test@example.com"], subject="Test Subject", text_content="Test content")

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert call_args["to"] == ["test@example.com"]
        assert call_args["subject"] == "Test Subject"
        assert call_args["body"] == "Test content"

    @patch("evan.models.emails.EmailLog.objects.create")
    def test_schedule_email_with_tags(self, mock_create):
        """Test scheduling email with tags."""
        user = UserFactory()
        event = EventFactory()

        schedule_email(
            to=["test@example.com"],
            subject="Test Subject",
            text_content="Test content",
            log_user=user,
            log_event=event,
            tags=["custom_tag"],
        )

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        expected_tags = [f"user.id:{user.pk}", f"event.id:{event.pk}", "custom_tag"]
        assert all(tag in call_args["tags"] for tag in expected_tags)

    @patch("evan.models.emails.EmailLog.objects.create")
    def test_schedule_email_duplicate_removal(self, mock_create):
        """Test that duplicate email addresses and tags are removed."""
        schedule_email(
            to=["test@example.com", "test@example.com", "other@example.com"],
            subject="Test Subject",
            text_content="Test content",
            bcc=["bcc@example.com", "bcc@example.com"],
            tags=["tag1", "tag1", "tag2"],
        )

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert len(call_args["to"]) == 2  # Duplicates removed
        assert len(call_args["bcc"]) == 1  # Duplicates removed
        assert len(call_args["tags"]) == 2  # Duplicates removed


@pytest.mark.django_db
class TestScheduleTemplateEmail:
    """Test the schedule_template_email function."""

    @patch("evan.services.mailer.base.schedule_email")
    def test_schedule_template_email_basic(self, mock_schedule):
        """Test scheduling template email."""
        template = EmailTemplateFactory(
            subject="Hello {{ name }}", body="Welcome {{ name }}!", from_email="test@example.com"
        )

        schedule_template_email(template=template, to=["recipient@example.com"], context={"name": "John"})

        mock_schedule.assert_called_once()
        call_args = mock_schedule.call_args[1]
        assert call_args["subject"] == "Hello John"
        assert call_args["text_content"] == "Welcome John!"
        assert call_args["from_email"] == "test@example.com"

    @patch("evan.services.mailer.base.schedule_email")
    def test_schedule_template_email_with_defaults(self, mock_schedule):
        """Test scheduling template email with defaults."""
        template = EmailTemplateFactory(
            subject="Test Subject",
            body="Test Body",
            from_email="",  # Empty to test default fallback
        )

        schedule_template_email(template=template, to=["recipient@example.com"])

        mock_schedule.assert_called_once()
        call_args = mock_schedule.call_args[1]
        assert call_args["from_email"] == "UGent <evan@ugent.be>"

    @patch("evan.services.mailer.base.schedule_email")
    @patch("evan.services.mailer.base.send_email_to_admins")
    def test_schedule_template_email_error_handling(self, mock_send_admin, mock_schedule):
        """Test error handling in schedule_template_email."""
        mock_schedule.side_effect = Exception("Test error")

        template = EmailTemplateFactory()

        with pytest.raises(Exception, match="Test error"):
            schedule_template_email(template=template, to=["recipient@example.com"])

        mock_send_admin.assert_called_once_with("Email error", "Error while sending email: Test error")
