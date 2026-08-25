"""Behaviour tests for the EmailPlan API: CRUD responses, preview, demo, send_now, logs.

We exercise the API as an event manager (the only role permitted) and assert
on the response payload and side effects (EmailLog rows, plan.sent_at).
"""

from http import HTTPStatus as status

import pytest
from django.urls import reverse

from evan.models import EmailLog, EmailPlan
from tests._factories import RegistrationFactory, UserFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _list_url(event) -> str:
    return event.get_api_url() + "emailplans/"


def _detail_url(plan) -> str:
    return reverse("v1:emailplan-detail", kwargs={"pk": plan.pk})


def _action_url(plan, action: str) -> str:
    return _list_url(plan.event) + f"{plan.pk}/{action}/"


@pytest.fixture
def manager_client(api_client, t_event_manager):
    """An api_client authenticated as an event manager."""
    api_client.force_authenticate(user=t_event_manager)
    return api_client


@pytest.fixture
def plan(t_event):
    """A draft EmailPlan on the shared event."""
    return EmailPlan.objects.create(
        event=t_event,
        name="Welcome plan",
        subject="Hello {{ user.first_name }}",
        body="Welcome to {{ event.name }}!",
        from_email="UGent <evan@ugent.be>",
        filters={},
    )


def _registration(t_event, *, user=None, fee_type=None):
    """Create an accepted registration on the shared event."""
    from datetime import UTC, datetime
    from unittest.mock import patch

    user = user or UserFactory()
    kwargs = {"event": t_event, "user": user}
    if fee_type is not None:
        kwargs["fee_type"] = fee_type
    with patch("django.utils.timezone.now", return_value=datetime(2026, 7, 1, 12, 0, tzinfo=UTC)):
        return RegistrationFactory(**kwargs)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanCRUD:
    """Create, list, retrieve, update, delete via the manager API."""

    def test_create_returns_201_and_links_event(self, manager_client, t_event, t_event_manager) -> None:
        data = {
            "name": "New plan",
            "subject": "Subject",
            "body": "Body",
            "from_email": "UGent <evan@ugent.be>",
            "filters": {"fee_types": ["regular"]},
            "is_draft": True,
        }
        response = manager_client.post(_list_url(t_event), data, format="json")

        assert response.status_code == status.CREATED
        assert "self" in response.data
        assert response.data["name"] == "New plan"
        assert response.data["recipients_count"] == 0  # no registrations yet
        plan = EmailPlan.objects.get(name="New plan")
        assert plan.event == t_event
        assert plan.created_by == t_event_manager

    def test_list_returns_all_plans_for_event(self, manager_client, t_event, plan) -> None:
        other = EmailPlan.objects.create(event=t_event, name="Other", subject="S", body="B", filters={})

        response = manager_client.get(_list_url(t_event))

        assert response.status_code == status.OK
        names = {p["name"] for p in response.data}
        assert names == {plan.name, other.name}

    def test_retrieve_returns_all_fields_including_body(self, manager_client, plan) -> None:
        response = manager_client.get(_detail_url(plan))

        assert response.status_code == status.OK
        assert response.data["body"] == plan.body
        assert response.data["subject"] == plan.subject

    def test_update_changes_fields(self, manager_client, plan) -> None:
        data = {
            "name": "Renamed",
            "subject": "New subject",
            "body": "New body",
            "from_email": "UGent <evan@ugent.be>",
            "filters": {"payment_status": "paid"},
            "send_at": "2026-09-01T10:00:00Z",
        }
        response = manager_client.put(_detail_url(plan), data, format="json")

        assert response.status_code == status.OK
        plan.refresh_from_db()
        assert plan.name == "Renamed"
        assert plan.send_at.isoformat().startswith("2026-09-01")

    def test_delete_removes_plan(self, manager_client, plan) -> None:
        response = manager_client.delete(_detail_url(plan))

        assert response.status_code == status.NO_CONTENT
        assert not EmailPlan.objects.filter(pk=plan.pk).exists()

    def test_recipients_count_reflects_filter(self, manager_client, t_event) -> None:
        _registration(t_event)
        _registration(t_event, user=UserFactory())

        data = {
            "name": "Count plan",
            "subject": "S",
            "body": "B",
            "filters": {},
        }
        response = manager_client.post(_list_url(t_event), data, format="json")

        assert response.data["recipients_count"] == 2


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanPreview:
    """The preview action renders subject + body against a random matching registration."""

    def test_preview_returns_rendered_subject_and_body(self, manager_client, t_event, plan) -> None:
        reg = _registration(t_event)

        response = manager_client.post(_action_url(plan, "preview"), format="json")

        assert response.status_code == status.OK
        assert response.data["subject"] == f"Hello {reg.user.first_name}"
        assert response.data["body"] == f"Welcome to {t_event.name}!"

    def test_preview_returns_404_when_no_registration_matches(self, manager_client, plan) -> None:
        plan.filters = {"fee_types": ["nonexistent"]}
        plan.save()

        response = manager_client.post(_action_url(plan, "preview"), format="json")

        assert response.status_code == status.NOT_FOUND


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanDemo:
    """The demo action creates a tagged EmailLog to the requesting user's inbox."""

    def test_demo_creates_tagged_log_to_manager(self, manager_client, t_event, plan, t_event_manager) -> None:
        _registration(t_event)  # a matching registration is required to render

        response = manager_client.post(_action_url(plan, "demo"), format="json")

        assert response.status_code == status.OK
        assert response.data["to"] == t_event_manager.email
        log = EmailLog.objects.get(to=[t_event_manager.email])
        assert f"emailplan.id:{plan.pk}" in log.tags
        assert "type:emailplan-demo" in log.tags

    def test_demo_returns_404_when_no_registration_matches(self, manager_client, plan) -> None:
        plan.filters = {"fee_types": ["nonexistent"]}
        plan.save()

        response = manager_client.post(_action_url(plan, "demo"), format="json")

        assert response.status_code == status.NOT_FOUND


# ---------------------------------------------------------------------------
# Send now
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanSendNow:
    """The send_now action resolves recipients, creates logs, marks sent_at."""

    def test_send_now_creates_one_log_per_recipient(self, manager_client, t_event, plan) -> None:
        r1 = _registration(t_event)
        r2 = _registration(t_event, user=UserFactory())

        response = manager_client.post(_action_url(plan, "send_now"), format="json")

        assert response.status_code == status.OK
        assert response.data["sent"] == 2
        plan.refresh_from_db()
        assert plan.sent_at is not None
        logs = EmailLog.objects.filter(tags__icontains=f"emailplan.id:{plan.pk}")
        assert logs.count() == 2
        to_addresses = {log.to[0] for log in logs}
        assert to_addresses == {r1.user.email, r2.user.email}

    def test_send_now_with_no_recipients_still_marks_sent(self, manager_client, plan) -> None:
        plan.filters = {"fee_types": ["nonexistent"]}
        plan.save()

        response = manager_client.post(_action_url(plan, "send_now"), format="json")

        assert response.status_code == status.OK
        assert response.data["sent"] == 0
        plan.refresh_from_db()
        assert plan.sent_at is not None


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanLogs:
    """The logs action returns only the EmailLog entries tagged with this plan."""

    def test_logs_returns_only_this_plans_emails(self, manager_client, t_event, plan) -> None:
        _registration(t_event)
        manager_client.post(_action_url(plan, "send_now"), format="json")

        # Create an unrelated email log on the same event.
        EmailLog.objects.create(event=t_event, from_email="x@x.be", to=["y@y.be"], subject="other", body="")

        response = manager_client.get(_action_url(plan, "logs"))

        assert response.status_code == status.OK
        assert len(response.data) == 1
        assert "type:emailplan" in response.data[0]["tags"]


# ---------------------------------------------------------------------------
# Flat viewset custom actions (plan.self + 'action/')
# ---------------------------------------------------------------------------


def _flat_action_url(plan, action: str) -> str:
    """Return the flat-viewset action URL (``/api/v1/emailplans/{pk}/{action}/``)."""
    return _detail_url(plan) + f"{action}/"


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanFlatActions:
    """Custom actions on the flat EmailPlanViewSet (plan.self + 'action/')."""

    def test_flat_preview_returns_rendered_subject_and_body(self, manager_client, t_event, plan) -> None:
        reg = _registration(t_event)

        response = manager_client.post(_flat_action_url(plan, "preview"), format="json")

        assert response.status_code == status.OK
        assert response.data["subject"] == f"Hello {reg.user.first_name}"
        assert response.data["body"] == f"Welcome to {t_event.name}!"

    def test_flat_demo_creates_tagged_log_to_manager(self, manager_client, t_event, plan, t_event_manager) -> None:
        _registration(t_event)

        response = manager_client.post(_flat_action_url(plan, "demo"), format="json")

        assert response.status_code == status.OK
        assert response.data["to"] == t_event_manager.email
        assert EmailLog.objects.filter(to=[t_event_manager.email]).exists()

    def test_flat_send_now_creates_logs_and_marks_sent(self, manager_client, t_event, plan) -> None:
        _registration(t_event)
        _registration(t_event, user=UserFactory())

        response = manager_client.post(_flat_action_url(plan, "send_now"), format="json")

        assert response.status_code == status.OK
        assert response.data["sent"] == 2
        plan.refresh_from_db()
        assert plan.sent_at is not None

    def test_flat_logs_returns_plan_emails(self, manager_client, t_event, plan) -> None:
        _registration(t_event)
        manager_client.post(_flat_action_url(plan, "send_now"), format="json")

        response = manager_client.get(_flat_action_url(plan, "logs"))

        assert response.status_code == status.OK
        assert len(response.data) == 1

    def test_flat_recipients_count_returns_count_for_request_filters(self, manager_client, t_event, plan) -> None:
        _registration(t_event)
        _registration(t_event, user=UserFactory())

        response = manager_client.post(
            _flat_action_url(plan, "recipients_count"),
            {"filters": {}},
            format="json",
        )

        assert response.status_code == status.OK
        assert response.data["count"] == 2

    def test_flat_recipients_count_reflects_fee_filter(self, manager_client, t_event, plan) -> None:
        from evan.models import Fee

        Fee.objects.create(event=t_event, type="regular", value=100)
        Fee.objects.create(event=t_event, type="student", value=50)
        _registration(t_event, fee_type="regular")
        _registration(t_event, user=UserFactory(), fee_type="student")

        response = manager_client.post(
            _flat_action_url(plan, "recipients_count"),
            {"filters": {"fee_types": ["regular"]}},
            format="json",
        )

        assert response.status_code == status.OK
        assert response.data["count"] == 1


# ---------------------------------------------------------------------------
# Event-scoped recipients_count (detail=False on nested viewset)
# ---------------------------------------------------------------------------


def _event_recipients_count_url(event) -> str:
    """Return the event-scoped recipients_count URL (``emailplans/recipients_count/``)."""
    return _list_url(event) + "recipients_count/"


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanEventRecipientsCount:
    """The event-scoped recipients_count action works without a saved plan."""

    def test_returns_count_for_filters(self, manager_client, t_event) -> None:
        _registration(t_event)
        _registration(t_event, user=UserFactory())

        response = manager_client.post(
            _event_recipients_count_url(t_event),
            {"filters": {}},
            format="json",
        )

        assert response.status_code == status.OK
        assert response.data["count"] == 2

    def test_zero_when_no_match(self, manager_client, t_event) -> None:
        _registration(t_event)

        response = manager_client.post(
            _event_recipients_count_url(t_event),
            {"filters": {"fee_types": ["nonexistent"]}},
            format="json",
        )

        assert response.status_code == status.OK
        assert response.data["count"] == 0


# ---------------------------------------------------------------------------
# List serializer (EmailPlanListSerializer omits body)
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.django_db
class TestEmailPlanListSerializer:
    """The list action uses EmailPlanListSerializer (no body field)."""

    def test_list_omits_body_field(self, manager_client, t_event, plan) -> None:
        response = manager_client.get(_list_url(t_event))

        assert response.status_code == status.OK
        assert "body" not in response.data[0]
        assert "subject" in response.data[0]
        assert "recipients_count" in response.data[0]
