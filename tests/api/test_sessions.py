from http import HTTPStatus as status

import pytest
from django.core.exceptions import ValidationError

from tests._factories import (
    EventFactory,
    PaperFactory,
    RoomFactory,
    SessionFactory,
    UserFactory,
    VenueFactory,
)


@pytest.fixture
def session(db, t_event):
    return SessionFactory(event=t_event)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
class TestForAnonymous:
    sees_secrets = False
    expected_status_codes: dict[str, status] = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.FORBIDDEN,
        "update": status.FORBIDDEN,
    }

    def _get_endpoint(self, event) -> str:
        return event.get_api_url() + "sessions/"

    def _get_create_data(self):
        return {}

    def _get_update_data(self):
        return {}

    def test_list(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list"]

    def test_retrieve(self, api_client, session) -> None:
        response = api_client.get(session.get_api_url())
        assert response.status_code == self.expected_status_codes["retrieve"]
        assert ("uuid" in response.data) is self.sees_secrets
        assert ("secret_url" in response.data) is self.sees_secrets

    def test_create(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        data = self._get_create_data()
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]

        if response.status_code == status.CREATED:
            assert response.data["title"] == data["title"].strip()

    def test_update(self, api_client, session) -> None:
        data = self._get_update_data()
        response = api_client.put(session.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestForUserWithEditLink(TestForAnonymous):
    expected_status_codes = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.FORBIDDEN,
        "update": status.OK,
    }

    def _get_update_data(self):
        return {
            "title": "Updated title",
        }

    def test_update(self, api_client, session) -> None:
        # This user uses an X-Evan-Secret header that allows them to edit the session
        api_client.credentials(HTTP_X_EVAN_SECRET=session.secret)
        data = self._get_update_data()
        response = api_client.put(session.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]


class TestForEventManager(TestForAuthenticated):
    sees_secrets = True
    expected_status_codes = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.CREATED,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def _get_create_data(self):
        return {
            "title": "Session title",
            "description": "Session description",
        }

    def _get_update_data(self):
        return {
            "title": "Updated title",
            "description": "Updated description",
        }

    def test_create_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        url = self._get_endpoint(other_event)
        response = api_client.post(url, self._get_create_data())
        assert response.status_code == status.FORBIDDEN

    def test_update_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        other_content = SessionFactory(event=other_event)
        response = api_client.put(other_content.get_api_url(), self._get_update_data())
        assert response.status_code == status.FORBIDDEN

    def test_delete(self, api_client, session) -> None:
        response = api_client.delete(session.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]

    def test_program_field_available_in_detail(self, api_client, t_event, session) -> None:
        """Test that program field is available in detail view."""
        session.program = "Session program includes detailed information."
        session.save()

        response = api_client.get(session.get_api_url())
        assert response.status_code == status.OK
        assert "program" in response.data
        assert response.data["program"] == "Session program includes detailed information."

    def test_program_validation_with_secrets(self, api_client, t_event, session) -> None:
        """Test that SessionWithSecretsSerializer includes program validation."""
        # Create a session with valid program first
        session.program = "Valid session program"
        session.save()

        # Since this test class has event manager auth, it should use SessionWithSecretsSerializer
        response = api_client.get(session.get_api_url())
        assert response.status_code == status.OK
        assert "program_validation" in response.data
        assert "program_paper_references" in response.data

        validation = response.data["program_validation"]
        assert validation["is_valid"] is True
        assert validation["paper_references"] == []

    def test_create_session_with_room(self, api_client, t_event) -> None:
        """Test creating a session with a room field."""
        venue = VenueFactory(event=t_event)
        room = RoomFactory(venue=venue)

        url = self._get_endpoint(t_event)
        data = {
            "title": "Session with room",
            "description": "This session has a room assigned",
            "room": room.id,
        }

        response = api_client.post(url, data)
        assert response.status_code == status.CREATED
        assert response.data["room"] == room.id

        # Verify the session was created with the correct room
        session_detail_url = response.data["self"]
        response = api_client.get(session_detail_url)
        assert response.status_code == status.OK
        assert response.data["room"] == room.id


@pytest.mark.api
class TestSessionPaperValidation:
    """Test session validation with paper references in program templates."""

    def test_session_validates_paper_references_on_save(self, db, t_event):
        """Test that sessions validate paper references when saved."""
        session = SessionFactory(event=t_event, program="", start_at=None, end_at=None)
        paper = PaperFactory(event=t_event, session=session, extra_data={"internal_id": "TEST123"})

        session.program = f"[paper:{paper.pk}] and [paperi:TEST123]"
        session.full_clean()
        session.save()

        assert paper.session == session

    def test_session_auto_assigns_papers_with_internal_id_references(self, db, t_event):
        """Test that papers are auto-assigned when referenced by internal ID."""
        session = SessionFactory(event=t_event, program="", start_at=None, end_at=None)
        paper = PaperFactory(event=t_event, session=session, extra_data={"internal_id": "AUTO123"})

        session.program = "[paperi:AUTO123]"
        session.full_clean()
        session.save()

        paper.refresh_from_db()
        assert paper.session == session

    def test_session_prevents_cross_session_paper_references(self, db, t_event):
        """Test that sessions cannot reference papers from other sessions."""
        from django.core.exceptions import ValidationError

        session1 = SessionFactory(event=t_event, start_at=None, end_at=None)
        session2 = SessionFactory(event=t_event, start_at=None, end_at=None)
        paper = PaperFactory(event=t_event, session=session1, extra_data={"internal_id": "CROSS123"})

        session2.program = f"[paper:{paper.pk}]"

        with pytest.raises(ValidationError) as exc_info:
            session2.full_clean()

        assert "already assigned to session" in str(exc_info.value)

    def test_session_handles_nonexistent_paper_references_gracefully(self, db, t_event):
        """Test that sessions handle references to nonexistent papers."""
        session = SessionFactory(event=t_event, start_at=None, end_at=None)

        session.program = "[paper:99999] and [paperi:NONEXISTENT]"

        # Should raise validation error for nonexistent paper
        with pytest.raises(ValidationError) as exc_info:
            session.full_clean()

        assert "99999" in str(exc_info.value)


@pytest.mark.api
class TestSessionBadgeIcon:
    """Test badge icon configuration through the session API endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_update_with_valid_badge_icon(self, api_client, session) -> None:
        """A whitelisted icon key is stored and returned."""
        payload = {"extra_data": {"badge_icon": "boat_trip"}}
        response = api_client.patch(session.get_api_url(), payload, format="json")

        assert response.status_code == status.OK
        assert response.data["extra_data"]["badge_icon"] == "boat_trip"

    def test_update_with_invalid_badge_icon(self, api_client, session) -> None:
        """An unknown icon key is rejected with a validation error."""
        response = api_client.patch(session.get_api_url(), {"extra_data": {"badge_icon": "not-an-icon"}}, format="json")

        assert response.status_code == status.BAD_REQUEST

    def test_empty_badge_icon_clears_icon(self, api_client, session) -> None:
        """An empty string clears the configured icon."""
        session.extra_data = {"badge_icon": "boat_trip"}
        session.save()

        response = api_client.patch(session.get_api_url(), {"extra_data": {"badge_icon": ""}}, format="json")

        assert response.status_code == status.OK
        assert response.data["extra_data"]["badge_icon"] is None
