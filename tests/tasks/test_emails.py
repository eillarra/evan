"""Tests for the huey email-sending task in evan.tasks.emails.

The email backend and admin-notifier are mocked at the boundary; we assert our
reaction to send success and the two failure branches.
"""

from datetime import UTC, datetime, timedelta
from smtplib import SMTPRecipientsRefused
from unittest.mock import patch

import pytest

from evan.models import EmailLog, EmailPlan
from evan.tasks.emails import process_email_plans, send_email, send_template_email
from tests._factories import EmailLogFactory, EventFactory, RegistrationFactory, UserFactory


@pytest.fixture(autouse=True)
def _no_sleep():
    """Avoid the real throttling sleep in tests."""
    with patch("evan.tasks.emails.sleep"):
        yield


@pytest.mark.django_db
class TestSendEmail:
    """Behaviour of the periodic send_email task."""

    def test_sends_pending_email_and_marks_sent(self):
        """A pending EmailLog is sent and its sent_at is set."""
        log = EmailLogFactory()

        with patch("evan.tasks.emails.EmailMultiAlternatives") as mock_msg:
            send_email.call_local()

        mock_msg.assert_called_once()
        # send() was called on the constructed message instance
        mock_msg.return_value.send.assert_called_once()
        log.refresh_from_db()
        assert log.sent_at is not None

    def test_recipient_refused_marks_epoch_and_notifies_admins_and_reraises(self):
        """SMTPRecipientsRefused sets sent_at to epoch 0, alerts admins, and re-raises."""
        log = EmailLogFactory()

        with (
            patch("evan.tasks.emails.EmailMultiAlternatives") as mock_msg,
            patch("evan.tasks.emails.send_email_to_admins") as mock_admins,
        ):
            mock_msg.return_value.send.side_effect = SMTPRecipientsRefused({"a@b.c": (550, "no")})
            with pytest.raises(SMTPRecipientsRefused):
                send_email.call_local()

        log.refresh_from_db()
        # epoch 0 is used to prevent retrying
        assert log.sent_at is not None
        assert log.sent_at.year == 1970
        mock_admins.assert_called_once()
        assert "Recipient refused" in mock_admins.call_args.args[1]

    def test_generic_exception_notifies_admins_and_reraises(self):
        """Any non-refused exception alerts admins and re-raises."""
        EmailLogFactory()

        with (
            patch("evan.tasks.emails.EmailMultiAlternatives") as mock_msg,
            patch("evan.tasks.emails.send_email_to_admins") as mock_admins,
        ):
            mock_msg.return_value.send.side_effect = RuntimeError("boom")
            with pytest.raises(RuntimeError):
                send_email.call_local()

        mock_admins.assert_called_once()
        assert "Error while sending email" in mock_admins.call_args.args[1]

    def test_does_not_send_already_sent_emails(self):
        """Emails with sent_at set are skipped."""
        log = EmailLogFactory()
        log.sent_at = log.created_at
        log.save()

        with patch("evan.tasks.emails.EmailMultiAlternatives") as mock_msg:
            send_email.call_local()

        mock_msg.assert_not_called()

    def test_attaches_html_alternative(self):
        """The markdown body is converted to HTML and attached."""
        EmailLogFactory(body="**bold**")

        with patch("evan.tasks.emails.EmailMultiAlternatives") as mock_msg:
            send_email.call_local()

        mock_msg.return_value.attach_alternative.assert_called_once()
        args, _ = mock_msg.return_value.attach_alternative.call_args
        assert "html" in args[1]
        assert "<strong>bold</strong>" in args[0]


@pytest.mark.django_db
class TestSendTemplateEmail:
    """Behaviour of send_template_email."""

    def test_schedules_email_with_rendered_body(self):
        """send_template_email schedules an EmailLog with the rendered message body."""
        context = {
            "message": "Hello attendees",
            "event_name": "My Event",
            "event_hashtag": "myevent",
            "sender_name": "Alice",
            "sender_affiliation": "UGent",
            "sender_email": "alice@ugent.be",
        }

        with patch("evan.tasks.emails.schedule_email") as mock_schedule:
            send_template_email(
                template_path="ignored",
                subject="Contact",
                from_email="alice@ugent.be",
                to=["bob@ugent.be"],
                context=context,
            )

        mock_schedule.assert_called_once()
        kwargs = mock_schedule.call_args.kwargs
        assert kwargs["from_email"] == "alice@ugent.be"
        assert kwargs["to"] == ["bob@ugent.be"]
        assert kwargs["subject"] == "Contact"
        assert "Hello attendees" in kwargs["text_content"]
        assert "My Event" in kwargs["text_content"]
        assert "Alice" in kwargs["text_content"]
        assert "alice@ugent.be" in kwargs["text_content"]

    def test_uses_defaults_for_missing_context_keys(self):
        """Missing context keys fall back to empty strings / 'Evan'."""
        with patch("evan.tasks.emails.schedule_email") as mock_schedule:
            send_template_email(
                template_path="ignored",
                subject="Contact",
                from_email="alice@ugent.be",
                to=["bob@ugent.be"],
                context={},
            )

        body = mock_schedule.call_args.kwargs["text_content"]
        assert "Evan" in body

    def test_actually_creates_email_log(self):
        """schedule_email is the real path; verify a log is created end-to-end."""
        send_template_email(
            template_path="ignored",
            subject="Contact",
            from_email="alice@ugent.be",
            to=["bob@ugent.be"],
            context={"message": "hi"},
        )

        log = EmailLog.objects.get()
        assert log.subject == "Contact"
        assert log.to == ["bob@ugent.be"]
        assert "hi" in log.body


@pytest.mark.django_db
class TestProcessEmailPlans:
    """Behaviour of the periodic process_email_plans task."""

    def _event_with_registration(self):
        """Create an event with one accepted registration for plan execution."""
        from evan.models import Fee

        event = EventFactory()
        Fee.objects.create(event=event, type="regular", value=100)
        user = UserFactory()
        with patch("django.utils.timezone.now", return_value=datetime(2026, 7, 1, 12, 0, tzinfo=UTC)):
            reg = RegistrationFactory(event=event, user=user)
        reg.is_accepted = True
        reg.save()
        return event

    def _make_plan(self, event, *, send_at=None, sent_at=None):
        """Create a saved EmailPlan with the given scheduling fields."""
        return EmailPlan.objects.create(
            event=event,
            name="Plan",
            subject="S",
            body="B",
            from_email="UGent <evan@ugent.be>",
            filters={},
            send_at=send_at,
            sent_at=sent_at,
        )

    def test_null_send_at_plan_is_not_processed(self):
        """A plan with no send_at is a draft and is skipped."""
        event = self._event_with_registration()
        self._make_plan(event, send_at=None)

        process_email_plans.call_local()

        plan = EmailPlan.objects.get(name="Plan")
        assert plan.sent_at is None
        assert EmailLog.objects.filter(event=event).count() == 0

    def test_future_send_at_plan_is_not_processed(self):
        """A plan with a future send_at is not processed yet."""
        event = self._event_with_registration()
        future = datetime.now(UTC) + timedelta(hours=1)
        self._make_plan(event, send_at=future)

        process_email_plans.call_local()

        plan = EmailPlan.objects.get(name="Plan")
        assert plan.sent_at is None

    def test_past_send_at_plan_is_processed(self):
        """A plan with a past send_at is processed."""
        event = self._event_with_registration()
        past = datetime.now(UTC) - timedelta(hours=1)
        self._make_plan(event, send_at=past)

        process_email_plans.call_local()

        plan = EmailPlan.objects.get(name="Plan")
        assert plan.sent_at is not None

    def test_already_sent_plan_is_not_processed_again(self):
        """A plan with sent_at set is skipped."""
        event = self._event_with_registration()
        past = datetime.now(UTC) - timedelta(hours=1)
        self._make_plan(event, send_at=past, sent_at=past)

        process_email_plans.call_local()

        assert EmailLog.objects.filter(event=event).count() == 0
