"""Tests for Album API."""

from http import HTTPStatus as status

import pytest

from tests._factories import AlbumFactory, RegistrationFactory, UserFactory


@pytest.fixture
def user(db):
    """Create a regular user for testing."""
    return UserFactory()


@pytest.fixture
def album(db, t_event):
    """Create a test album."""
    return AlbumFactory(event=t_event)


@pytest.mark.api
class TestForAnonymous:
    """Test album endpoints for anonymous users."""

    expected_status_codes: dict[str, status] = {
        "list_albums": status.FORBIDDEN,
        "retrieve_album": status.FORBIDDEN,
    }

    def test_list_albums(self, api_client, t_event):
        """Test that anonymous users cannot access albums."""
        url = f"/api/v1/events/{t_event.code}/albums/"
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list_albums"]

    def test_retrieve_album(self, api_client, album):
        """Test that anonymous users cannot retrieve album details."""
        url = f"/api/v1/albums/{album.id}/"
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["retrieve_album"]


class TestForAuthenticated(TestForAnonymous):
    """Test album endpoints for authenticated users (not necessarily attendees)."""

    expected_status_codes = {
        "list_albums": status.FORBIDDEN,
        "retrieve_album": status.FORBIDDEN,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestForAttendee(TestForAuthenticated):
    """Test album endpoints for users who are registered attendees."""

    expected_status_codes = {
        "list_albums": status.OK,
        "retrieve_album": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user, t_event):
        api_client.force_authenticate(user=user)
        # Make the user an attendee of the event
        RegistrationFactory(event=t_event, user=user, is_accepted=True, no_show=False)

    def test_list_albums(self, api_client, t_event, album):
        """Test that attendees can list albums."""
        url = f"/api/v1/events/{t_event.code}/albums/"
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list_albums"]
        assert len(response.data) == 1
        assert response.data[0]["title"] == album.title

    def test_retrieve_album(self, api_client, album):
        """Test that attendees can retrieve album details."""
        url = f"/api/v1/albums/{album.id}/"
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["retrieve_album"]
        assert response.data["title"] == album.title


class TestForNoShowUser(TestForAuthenticated):
    """Test album endpoints for users who are registered but marked as no-show."""

    expected_status_codes = {
        "list_albums": status.FORBIDDEN,
        "retrieve_album": status.FORBIDDEN,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user, t_event):
        api_client.force_authenticate(user=user)
        # Make the user a no-show attendee
        RegistrationFactory(event=t_event, user=user, is_accepted=True, no_show=True)


class TestForEventManager(TestForAttendee):
    """Test album endpoints for event managers."""

    expected_status_codes = {
        "list_albums": status.OK,
        "retrieve_album": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)
