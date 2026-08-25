"""Tests for EmailPlan API endpoint permissions.

Covers the two-part API:
  - EmailPlansViewSet → list/create/update/delete at /events/{code}/emailplans/
    and custom actions (preview, demo, send_now, logs) at the same prefix.
  - EmailPlanViewSet  → retrieve/update/delete at /emailplans/{pk}/
"""

from http import HTTPStatus as status

import pytest
from django.urls import reverse

from evan.models import EmailPlan
from tests._factories import UserFactory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def emailplan(db, t_event):
    """A draft EmailPlan belonging to the shared test event."""
    return EmailPlan.objects.create(
        event=t_event,
        name="Welcome plan",
        subject="Hello {{ user.first_name }}",
        body="Welcome to {{ event.name }}!",
        from_email="UGent <evan@ugent.be>",
        filters={},
    )


@pytest.fixture
def user(db):
    """A regular authenticated user with no event permissions."""
    return UserFactory()


def _list_url(event) -> str:
    return event.get_api_url() + "emailplans/"


def _detail_url(plan) -> str:
    return reverse("v1:emailplan-detail", kwargs={"pk": plan.pk})


def _action_url(plan, action: str) -> str:
    return _list_url(plan.event) + f"{plan.pk}/{action}/"


# ---------------------------------------------------------------------------
# List + create (EmailPlansViewSet)
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestEmailPlansListCreateForAnonymous:
    """Anonymous users are blocked from listing and creating email plans."""

    expected_status_codes: dict[str, status] = {
        "list": status.FORBIDDEN,
        "create": status.FORBIDDEN,
    }

    def test_list(self, api_client, t_event) -> None:
        response = api_client.get(_list_url(t_event))
        assert response.status_code == self.expected_status_codes["list"]

    def test_create(self, api_client, t_event) -> None:
        data = {
            "name": "New plan",
            "subject": "Subject",
            "body": "Body",
            "filters": {},
        }
        response = api_client.post(_list_url(t_event), data, format="json")
        assert response.status_code == self.expected_status_codes["create"]


class TestEmailPlansListCreateForAuthenticated(TestEmailPlansListCreateForAnonymous):
    """Authenticated non-managers are blocked too."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestEmailPlansListCreateForEventManager(TestEmailPlansListCreateForAuthenticated):
    """Event managers can list and create email plans."""

    expected_status_codes = {
        "list": status.OK,
        "create": status.CREATED,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_create_persists_correctly(self, api_client, t_event, t_event_manager) -> None:
        """Created plan is saved with the correct event and created_by."""
        data = {
            "name": "New plan",
            "subject": "Subject",
            "body": "Body",
            "filters": {"fee_types": ["regular"]},
        }
        response = api_client.post(_list_url(t_event), data, format="json")

        assert response.status_code == status.CREATED
        plan = EmailPlan.objects.get(event=t_event, name="New plan")
        assert plan.created_by == t_event_manager
        assert plan.filters == {"fee_types": ["regular"]}


# ---------------------------------------------------------------------------
# Detail: retrieve / update / delete (EmailPlanViewSet)
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestEmailPlanDetailForAnonymous:
    """Anonymous users cannot retrieve or modify individual email plans."""

    expected_status_codes: dict[str, status] = {
        "retrieve": status.FORBIDDEN,
        "update": status.FORBIDDEN,
        "delete": status.FORBIDDEN,
    }

    def test_retrieve(self, api_client, emailplan) -> None:
        response = api_client.get(_detail_url(emailplan))
        assert response.status_code == self.expected_status_codes["retrieve"]

    def test_update(self, api_client, emailplan) -> None:
        data = {"name": "Renamed", "subject": "S", "body": "B", "filters": {}}
        response = api_client.put(_detail_url(emailplan), data, format="json")
        assert response.status_code == self.expected_status_codes["update"]

    def test_delete(self, api_client, emailplan) -> None:
        response = api_client.delete(_detail_url(emailplan))
        assert response.status_code == self.expected_status_codes["delete"]


class TestEmailPlanDetailForAuthenticated(TestEmailPlanDetailForAnonymous):
    """Non-manager authenticated users are also blocked."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestEmailPlanDetailForEventManager(TestEmailPlanDetailForAuthenticated):
    """Event managers can retrieve, update, and delete email plans."""

    expected_status_codes = {
        "retrieve": status.OK,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_update_persists_correctly(self, api_client, emailplan) -> None:
        data = {"name": "Renamed plan", "subject": "S", "body": "B", "filters": {}}
        api_client.put(_detail_url(emailplan), data, format="json")

        emailplan.refresh_from_db()
        assert emailplan.name == "Renamed plan"


# ---------------------------------------------------------------------------
# Custom actions permissions (preview / demo / send_now / logs)
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestEmailPlanActionsForAnonymous:
    """Anonymous users are blocked from all custom actions."""

    expected_status_codes: dict[str, status] = {
        "preview": status.FORBIDDEN,
        "demo": status.FORBIDDEN,
        "send_now": status.FORBIDDEN,
        "logs": status.FORBIDDEN,
    }

    def test_preview(self, api_client, emailplan) -> None:
        response = api_client.post(_action_url(emailplan, "preview"), format="json")
        assert response.status_code == self.expected_status_codes["preview"]

    def test_demo(self, api_client, emailplan) -> None:
        response = api_client.post(_action_url(emailplan, "demo"), format="json")
        assert response.status_code == self.expected_status_codes["demo"]

    def test_send_now(self, api_client, emailplan) -> None:
        response = api_client.post(_action_url(emailplan, "send_now"), format="json")
        assert response.status_code == self.expected_status_codes["send_now"]

    def test_logs(self, api_client, emailplan) -> None:
        response = api_client.get(_action_url(emailplan, "logs"))
        assert response.status_code == self.expected_status_codes["logs"]


class TestEmailPlanActionsForAuthenticated(TestEmailPlanActionsForAnonymous):
    """Non-manager authenticated users are also blocked."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)
