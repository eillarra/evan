"""Tests for sponsor API endpoint permissions.

Covers the two-part sponsor API:
  - SponsorsViewSet → GET/POST /events/{code}/sponsors/  (event-manager only)
  - SponsorViewSet  → GET/PUT/DELETE /sponsors/{pk}/     (event-manager only)
"""

from http import HTTPStatus as status

import pytest
from django.urls import reverse

from evan.models import Sponsor
from tests._factories import UserFactory


@pytest.fixture
def sponsor(db, t_event):
    """A sponsor belonging to the shared test event."""
    return Sponsor.objects.create(event=t_event, name="ACME Corp", website="https://acme.example.com", level=1)


@pytest.fixture
def user(db):
    """A regular authenticated user with no event permissions."""
    return UserFactory()


def _list_url(event) -> str:
    return event.get_api_url() + "sponsors/"


def _detail_url(sponsor) -> str:
    return reverse("v1:sponsor-detail", kwargs={"pk": sponsor.pk})


# ---------------------------------------------------------------------------
# SponsorsViewSet — list and create
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestSponsorsListCreateForAnonymous:
    """Anonymous users are blocked from both listing and creating sponsors."""

    expected_status_codes: dict[str, status] = {
        "list": status.FORBIDDEN,
        "create": status.FORBIDDEN,
    }

    def test_list(self, api_client, t_event) -> None:
        response = api_client.get(_list_url(t_event))
        assert response.status_code == self.expected_status_codes["list"]

    def test_create(self, api_client, t_event) -> None:
        data = {"name": "New Sponsor", "website": "https://new.example.com", "level": 2}
        response = api_client.post(_list_url(t_event), data)
        assert response.status_code == self.expected_status_codes["create"]


class TestSponsorsListCreateForAuthenticated(TestSponsorsListCreateForAnonymous):
    """Authenticated users without event permissions are also blocked."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestSponsorsListCreateForEventManager(TestSponsorsListCreateForAuthenticated):
    """Event managers can list and create sponsors."""

    expected_status_codes = {
        "list": status.OK,
        "create": status.CREATED,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_create_persists_correctly(self, api_client, t_event) -> None:
        """Created sponsor is saved with the correct event association."""
        data = {"name": "New Sponsor", "website": "https://new.example.com", "level": 2}
        response = api_client.post(_list_url(t_event), data)

        assert response.status_code == status.CREATED
        assert Sponsor.objects.filter(event=t_event, name="New Sponsor").exists()


# ---------------------------------------------------------------------------
# SponsorViewSet — retrieve, update, delete
# ---------------------------------------------------------------------------


@pytest.mark.api
class TestSponsorDetailForAnonymous:
    """Anonymous users cannot retrieve or modify individual sponsors."""

    expected_status_codes: dict[str, status] = {
        "retrieve": status.FORBIDDEN,
        "update": status.FORBIDDEN,
        "delete": status.FORBIDDEN,
    }

    def test_retrieve(self, api_client, sponsor) -> None:
        response = api_client.get(_detail_url(sponsor))
        assert response.status_code == self.expected_status_codes["retrieve"]

    def test_update(self, api_client, sponsor) -> None:
        data = {"name": "Updated", "website": "https://updated.example.com", "level": 1}
        response = api_client.put(_detail_url(sponsor), data)
        assert response.status_code == self.expected_status_codes["update"]

    def test_delete(self, api_client, sponsor) -> None:
        response = api_client.delete(_detail_url(sponsor))
        assert response.status_code == self.expected_status_codes["delete"]


class TestSponsorDetailForAuthenticated(TestSponsorDetailForAnonymous):
    """Non-manager authenticated users are also blocked."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestSponsorDetailForEventManager(TestSponsorDetailForAuthenticated):
    """Event managers can retrieve, update, and delete sponsors."""

    expected_status_codes = {
        "retrieve": status.OK,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_update_persists_correctly(self, api_client, sponsor) -> None:
        """Update changes are saved to the database."""
        data = {"name": "Renamed Sponsor", "website": "https://renamed.example.com", "level": 3}
        api_client.put(_detail_url(sponsor), data)

        sponsor.refresh_from_db()
        assert sponsor.name == "Renamed Sponsor"
        assert sponsor.level == 3
