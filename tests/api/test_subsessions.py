from datetime import timedelta
from http import HTTPStatus as status

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from evan.models import Subsession
from evan.utils.factories import EventFactory, PaperFactory, SessionFactory, UserFactory


@pytest.fixture
def session(db, t_event):
    return SessionFactory(event=t_event)


@pytest.fixture
def subsession(db, session):
    return Subsession.objects.create(
        session=session,
        title="Morning Session",
        order=1,
    )


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

    def _get_endpoint(self, session) -> str:
        return reverse("v1:session-subsessions-list", args=[session.pk])

    def _get_create_data(self):
        return {"title": "Test Subsession", "order": 1}

    def _get_update_data(self):
        return {"title": "Updated Subsession"}

    def test_list(self, api_client, session) -> None:
        url = self._get_endpoint(session)
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list"]

    def test_retrieve(self, api_client, subsession) -> None:
        url = reverse("v1:subsession-detail", args=[subsession.pk])
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["retrieve"]
        assert ("uuid" in response.data) is self.sees_secrets

    def test_create(self, api_client, session) -> None:
        url = self._get_endpoint(session)
        response = api_client.post(url, self._get_create_data())
        assert response.status_code == self.expected_status_codes["create"]

    def test_update(self, api_client, subsession) -> None:
        url = reverse("v1:subsession-detail", args=[subsession.pk])
        data = self._get_update_data()
        response = api_client.put(url, data)
        assert response.status_code == self.expected_status_codes["update"]


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


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
            "title": "Test Subsession",
            "order": 1,
        }

    def _get_update_data(self):
        return {
            "title": "Updated Subsession",
        }

    def test_create_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        other_session = SessionFactory(event=other_event)
        url = self._get_endpoint(other_session)
        response = api_client.post(url, self._get_create_data())
        assert response.status_code == status.FORBIDDEN

    def test_update_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        other_session = SessionFactory(event=other_event)
        other_subsession = Subsession.objects.create(
            session=other_session,
            title="Other Subsession",
            order=1,
        )
        url = reverse("v1:subsession-detail", args=[other_subsession.pk])
        response = api_client.put(url, self._get_update_data())
        assert response.status_code == status.FORBIDDEN

    def test_delete(self, api_client, subsession) -> None:
        url = reverse("v1:subsession-detail", args=[subsession.pk])
        response = api_client.delete(url)
        assert response.status_code == self.expected_status_codes["delete"]

    def test_datetime_validation_start_before_session(self, api_client, session) -> None:
        event = session.event

        session_start_dt = event.start_date + timedelta(hours=2)
        session_end_dt = event.start_date + timedelta(hours=5)

        if session_end_dt > event.end_date:
            session_end_dt = event.end_date - timedelta(minutes=1)
        if session_start_dt >= session_end_dt:
            session_start_dt = event.start_date
            session_end_dt = event.start_date + timedelta(minutes=30)
            if session_end_dt > event.end_date:
                session_end_dt = event.end_date

        session.start_at = session_start_dt
        session.end_at = session_end_dt
        session.save()

        url = self._get_endpoint(session)

        invalid_start_for_subsession = session.start_at - timedelta(hours=1)
        if invalid_start_for_subsession < event.start_date:
            invalid_start_for_subsession = event.start_date

        data = {
            "title": "Invalid Subsession",
            "order": 1,
            "start_at": invalid_start_for_subsession.isoformat(),
        }
        response = api_client.post(url, data)
        assert response.status_code == status.BAD_REQUEST

        error_data = response.json()
        assert "start_at" in error_data, f"Expected 'start_at' in response errors, got {error_data}"
        assert any(
            "Subsession start time cannot be before session start time" in str(e) for e in error_data["start_at"]
        ), f"Unexpected error for start_at: {error_data['start_at']}"

    def test_datetime_validation_end_after_session(self, api_client, session) -> None:
        event = session.event

        session_start_dt = event.start_date + timedelta(hours=2)
        session_end_dt = event.start_date + timedelta(hours=5)

        if session_end_dt > event.end_date:
            session_end_dt = event.end_date - timedelta(minutes=1)
        if session_start_dt >= session_end_dt:
            session_start_dt = event.start_date
            session_end_dt = event.start_date + timedelta(minutes=30)
            if session_end_dt > event.end_date:
                session_end_dt = event.end_date

        session.start_at = session_start_dt
        session.end_at = session_end_dt
        session.save()

        url = self._get_endpoint(session)

        invalid_end_for_subsession = session.end_at + timedelta(hours=1)
        if invalid_end_for_subsession > event.end_date:
            invalid_end_for_subsession = event.end_date

        data = {
            "title": "Invalid Subsession",
            "order": 1,
            "end_at": invalid_end_for_subsession.isoformat(),
        }
        response = api_client.post(url, data)
        assert response.status_code == status.BAD_REQUEST
        assert "end_at" in response.data, f"Response data: {response.data}"
        assert "after session end time" in str(response.data["end_at"])

    def test_datetime_validation_valid_times(self, api_client, session) -> None:
        event = session.event

        session_start_dt = event.start_date + timedelta(hours=2)
        session_end_dt = event.start_date + timedelta(hours=5)

        if session_end_dt > event.end_date:
            session_end_dt = event.end_date - timedelta(minutes=1)
        if session_start_dt >= session_end_dt:
            session_start_dt = event.start_date
            session_end_dt = event.start_date + timedelta(minutes=30)
            if session_end_dt > event.end_date:
                session_end_dt = event.end_date

        session.start_at = session_start_dt
        session.end_at = session_end_dt
        session.save()

        url = self._get_endpoint(session)

        valid_subsession_start = session.start_at + timedelta(minutes=30)
        valid_subsession_end = session.end_at - timedelta(minutes=30)

        if valid_subsession_start >= valid_subsession_end:
            valid_subsession_end = valid_subsession_start + timedelta(minutes=1)
            if valid_subsession_end > session.end_at:
                valid_subsession_end = session.end_at
            if valid_subsession_start >= valid_subsession_end and session.start_at < session.end_at:
                valid_subsession_start = session.start_at

        data = {
            "title": "Valid Subsession",
            "order": 1,
            "start_at": valid_subsession_start.isoformat(),
            "end_at": valid_subsession_end.isoformat(),
        }
        response = api_client.post(url, data)
        assert response.status_code == status.CREATED, f"Response data: {response.data}"

        created_subsession = Subsession.objects.get(id=response.data["id"])
        assert created_subsession.start_at is not None
        assert created_subsession.end_at is not None
        assert session.start_at is not None
        assert session.end_at is not None
        assert created_subsession.start_at >= session.start_at
        assert created_subsession.end_at <= session.end_at
        assert created_subsession.start_at < created_subsession.end_at


@pytest.mark.api
class TestSubsessionPaperValidation:
    """Test subsession validation with paper references in program templates."""

    def test_subsession_validates_paper_references_on_save(self, db, t_event):
        """Test that subsessions validate paper references when saved."""
        session = SessionFactory(event=t_event)
        subsession = Subsession.objects.create(
            session=session,
            title="Test Subsession",
            order=1,
            program="",
        )
        paper = PaperFactory(event=t_event, session=session, extra_data={"internal_id": "SUB123"})

        subsession.program = f"[paper:{paper.pk}] and [paperi:SUB123]"
        subsession.full_clean()
        subsession.save()

        assert paper.session == session

    def test_subsession_auto_assigns_papers_with_internal_id_references(self, db, t_event):
        """Test that papers are auto-assigned to subsessions when referenced by internal ID."""
        session = SessionFactory(event=t_event)
        subsession = Subsession.objects.create(
            session=session,
            title="Test Subsession",
            order=1,
            program="",
        )
        # Create paper without session/subsession assignment for auto-assignment to work
        paper = PaperFactory(event=t_event, session=None, extra_data={"internal_id": "SUBASSIGN123"})

        subsession.program = "[paperi:SUBASSIGN123]"
        subsession.full_clean()
        subsession.save()

        paper.refresh_from_db()
        assert paper.subsession == subsession

    def test_subsession_prevents_cross_subsession_paper_references(self, db, t_event):
        """Test that subsessions cannot reference papers from other subsessions."""
        session = SessionFactory(event=t_event)
        subsession1 = Subsession.objects.create(session=session, title="Subsession 1", order=1)
        subsession2 = Subsession.objects.create(session=session, title="Subsession 2", order=2)
        paper = PaperFactory(
            event=t_event, session=session, subsession=subsession1, extra_data={"internal_id": "SUBCROSS123"}
        )

        subsession2.program = f"[paper:{paper.pk}]"

        with pytest.raises(ValidationError) as exc_info:
            subsession2.full_clean()

        assert "already assigned to" in str(exc_info.value)
