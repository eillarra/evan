"""Tests for the communications-module guard on email plan execution."""

import logging
from datetime import UTC, datetime, timedelta

import pytest

from evan.models import EmailLog, EmailPlan
from evan.services.mailer.emailplans import execute_plan
from tests._factories import EventFactory, RegistrationFactory, UserFactory


@pytest.mark.django_db
class TestExecutePlanCommunicationsGuard:
    """Email plans on communications-disabled events never send."""

    def _due_plan(self, event) -> EmailPlan:
        plan = EmailPlan.objects.create(
            event=event,
            name="Plan",
            subject="Subject",
            body="Body",
            send_at=datetime.now(UTC) - timedelta(hours=1),
        )
        RegistrationFactory(event=event, user=UserFactory(), fee_type="regular", is_accepted=True)
        return plan

    def test_disabled_communications_skips_send_and_logs(self, caplog):
        event = EventFactory(config={"modules": {}})

        plan = self._due_plan(event)

        with caplog.at_level(logging.INFO, logger="evan.services.mailer.emailplans"):
            created = execute_plan(plan)

        assert created == 0
        assert "communications" in caplog.text
        plan.refresh_from_db()
        assert plan.sent_at is None
        assert EmailLog.objects.filter(event=event).count() == 0

    def test_enabled_communications_still_sends(self):
        event = EventFactory(config={"modules": {"communications": True}})

        plan = self._due_plan(event)

        created = execute_plan(plan)

        assert created == 1
        plan.refresh_from_db()
        assert plan.sent_at is not None
        assert EmailLog.objects.filter(event=event, tags__icontains="type:emailplan").count() == 1
