"""Tests for Event API endpoints."""

from http import HTTPStatus as status

import pytest

from evan.utils.factories import RegistrationFactory, UserFactory


@pytest.fixture
def user(db):
    """Create a regular user for testing."""
    return UserFactory()


@pytest.mark.api
class TestForAnonymous:
    """Test event endpoints for anonymous users."""

    expected_status_codes: dict[str, status] = {
        "retrieve": status.OK,
        "update": status.FORBIDDEN,
        "attendees": status.FORBIDDEN,
        "contact": status.FORBIDDEN,
    }

    def _get_update_data(self):
        return {"name": "Updated Event Name"}

    def test_retrieve(self, api_client, t_event):
        """Test retrieving event details without authentication."""
        url = t_event.get_api_url()
        response = api_client.get(url)

        assert response.status_code == self.expected_status_codes["retrieve"]
        data = response.json()
        assert data["name"] == t_event.name
        assert data["code"] == t_event.code
        assert "venues" in data
        assert "topics" in data
        assert "tracks" in data

    def test_update(self, api_client, t_event):
        """Test updating event without authentication fails."""
        url = t_event.get_api_url()
        data = self._get_update_data()
        response = api_client.patch(url, data)

        assert response.status_code == self.expected_status_codes["update"]

    def test_attendees_list(self, api_client, t_event):
        """Test attendees list without authentication fails."""
        url = t_event.get_api_url() + "attendees/"
        response = api_client.get(url)

        assert response.status_code == self.expected_status_codes["attendees"]

    def test_contact_attendee(self, api_client, t_event):
        """Test contacting attendee without authentication fails."""
        url = t_event.get_api_url() + "contact/"
        data = {"user_id": 1, "message": "Hello!"}
        response = api_client.post(url, data)

        assert response.status_code == self.expected_status_codes["contact"]


class TestForAuthenticated(TestForAnonymous):
    """Test event endpoints for authenticated users (not necessarily attendees)."""

    expected_status_codes = {
        "retrieve": status.OK,
        "update": status.FORBIDDEN,
        "attendees": status.FORBIDDEN,
        "contact": status.FORBIDDEN,  # Non-attendees cannot contact attendees
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)

    def test_contact_attendee(self, api_client, t_event, user):
        """Test contacting attendee as authenticated but non-attendee user fails."""
        target_user = UserFactory()
        RegistrationFactory(event=t_event, user=target_user, fee_type="regular")

        url = t_event.get_api_url() + "contact/"
        data = {"user_id": target_user.id, "message": "Hello!"}
        response = api_client.post(url, data)

        # Should fail because user is not an attendee
        assert response.status_code == self.expected_status_codes["contact"]


class TestForAttendee(TestForAuthenticated):
    """Test event endpoints for users who are registered attendees."""

    expected_status_codes = {
        "retrieve": status.OK,
        "update": status.FORBIDDEN,
        "attendees": status.OK,  # Attendees can see other attendees
        "contact": status.OK,  # Attendees can contact other attendees
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user, t_event):
        api_client.force_authenticate(user=user)
        # Make the user an attendee of the event
        RegistrationFactory(event=t_event, user=user, fee_type="regular")

    def test_contact_attendee_success(self, api_client, t_event, user, monkeypatch):
        """Test contacting another attendee as an attendee."""
        # Create another attendee to contact
        target_user = UserFactory()
        RegistrationFactory(event=t_event, user=target_user, fee_type="regular")

        # Mock the email sending task
        monkeypatch.setattr("evan.tasks.emails.send_template_email", lambda *args, **kwargs: None)

        url = t_event.get_api_url() + "contact/"
        data = {"user_id": target_user.id, "message": "Hello, fellow attendee!"}
        response = api_client.post(url, data)

        assert response.status_code == status.OK
        assert "Your message has been sent" in response.json()["detail"]

    def test_contact_attendee_not_registered(self, api_client, t_event, user):
        """Test contacting user not registered for event fails."""
        target_user = UserFactory()

        url = t_event.get_api_url() + "contact/"
        data = {"user_id": target_user.id, "message": "Hello!"}
        response = api_client.post(url, data)

        assert response.status_code == status.FORBIDDEN
        assert "cannot be contacted" in response.json()["detail"]


class TestForEventManager(TestForAttendee):
    """Test event endpoints for event managers."""

    expected_status_codes = {
        "retrieve": status.OK,
        "update": status.OK,
        "attendees": status.OK,
        "contact": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_update(self, api_client, t_event):
        """Test updating event as event manager."""
        url = t_event.get_api_url()
        data = self._get_update_data()
        response = api_client.patch(url, data)

        assert response.status_code == self.expected_status_codes["update"]
        t_event.refresh_from_db()
        assert t_event.name == "Updated Event Name"

    def test_attendees_list(self, api_client, t_event):
        """Test retrieving event attendees as manager."""
        # Create some registrations
        user1 = UserFactory()
        user2 = UserFactory()
        RegistrationFactory(event=t_event, user=user1, fee_type="regular")
        RegistrationFactory(event=t_event, user=user2, fee_type="regular")

        url = t_event.get_api_url() + "attendees/"
        response = api_client.get(url)

        assert response.status_code == self.expected_status_codes["attendees"]
        data = response.json()
        assert len(data) >= 2  # At least our 2 test users

    def test_contact_attendee(self, api_client, t_event, t_event_manager):
        """Test contacting users as event manager."""
        # Event managers can contact registered users even if they don't allow contact
        target_user = UserFactory()
        RegistrationFactory(event=t_event, user=target_user, fee_type="regular")

        url = t_event.get_api_url() + "contact/"
        data = {"user_id": target_user.id, "message": "Hello from the event organizer!"}
        response = api_client.post(url, data)

        # Should succeed for event managers contacting registered users
        assert response.status_code == self.expected_status_codes["contact"]
        assert "Your message has been sent" in response.json()["detail"]

    def test_contact_non_registered_user_fails(self, api_client, t_event, t_event_manager):
        """Test that event managers cannot contact users not registered for their event."""
        # Create a user who is NOT registered for this event
        target_user = UserFactory()

        url = t_event.get_api_url() + "contact/"
        data = {"user_id": target_user.id, "message": "Hello!"}
        response = api_client.post(url, data)

        # Should fail because target user is not registered for this event
        assert response.status_code == status.FORBIDDEN
        assert "cannot be contacted" in response.json()["detail"]
