"""
Integration tests for the complete program template assignment workflow.

Tests the critical workflow:
1. Create paper/keynote
2. Create session with program referencing paper/keynote
3. Check that the paper/keynote has the right session/subsession assigned
"""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from tests._factories import KeynoteFactory, PaperFactory, SessionFactory, SubsessionFactory


@pytest.mark.api
class TestProgramAssignmentWorkflow:
    """Test the complete workflow of program template references and auto-assignment."""

    def test_session_api_assigns_paper_by_id(self, api_client, t_event_manager, t_event):
        """Test API workflow: create paper, create session referencing paper, verify assignment."""
        api_client.force_authenticate(user=t_event_manager)

        # 1. Create paper
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        # 2. Create session via API with program referencing paper
        session_data = {
            "title": "Test Session",
            "program": f"Welcome to our session.\n\n[paper:{paper.pk}]\n\nThank you.",
        }
        response = api_client.post(t_event.get_api_url() + "sessions/", session_data)
        assert response.status_code == 201

        # 3. Check that paper has been assigned to session
        paper.refresh_from_db()
        session_id = response.data["id"]
        assert paper.session_id == session_id
        assert paper.subsession is None

    def test_session_api_assigns_paper_by_internal_id(self, api_client, t_event_manager, t_event):
        """Test API workflow: create paper with internal_id, reference by internal_id, verify assignment."""
        api_client.force_authenticate(user=t_event_manager)

        # 1. Create paper with internal_id
        paper = PaperFactory(event=t_event, session=None, subsession=None, extra_data={"internal_id": "PAPER-001"})

        # 2. Create session via API with program referencing paper by internal_id
        session_data = {
            "title": "Test Session",
            "program": "Welcome to our session.\n\n[paperi:PAPER-001]\n\nThank you.",
        }
        response = api_client.post(t_event.get_api_url() + "sessions/", session_data)
        assert response.status_code == 201

        # 3. Check that paper has been assigned to session
        paper.refresh_from_db()
        session_id = response.data["id"]
        assert paper.session_id == session_id
        assert paper.subsession is None

    def test_session_api_assigns_keynote_by_code(self, api_client, t_event_manager, t_event):
        """Test API workflow: create keynote, create session referencing keynote, verify assignment."""
        api_client.force_authenticate(user=t_event_manager)

        # 1. Create keynote
        keynote = KeynoteFactory(event=t_event, code="KEYNOTE-001", session=None, subsession=None)

        # 2. Create session via API with program referencing keynote
        session_data = {
            "title": "Test Session",
            "program": "Welcome to our session.\n\n[keynote:KEYNOTE-001]\n\nThank you.",
        }
        response = api_client.post(t_event.get_api_url() + "sessions/", session_data)
        assert response.status_code == 201

        # 3. Check that keynote has been assigned to session
        keynote.refresh_from_db()
        session_id = response.data["id"]
        assert keynote.session_id == session_id
        assert keynote.subsession is None

    def test_subsession_api_assigns_paper_by_id(self, api_client, t_event_manager, t_event):
        """Test API workflow: create paper, create subsession referencing paper, verify assignment."""
        api_client.force_authenticate(user=t_event_manager)

        # 1. Create paper and session
        session = SessionFactory(event=t_event)
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        # 2. Create subsession via API with program referencing paper
        subsession_data = {
            "title": "Test Subsession",
            "program": f"Welcome to our subsession.\n\n[paper:{paper.pk}]\n\nThank you.",
        }
        response = api_client.post(reverse("v1:session-subsessions-list", args=[session.pk]), subsession_data)
        assert response.status_code == 201

        # 3. Check that paper has been assigned to session and subsession
        paper.refresh_from_db()
        subsession_id = response.data["id"]
        assert paper.session_id == session.pk
        assert paper.subsession_id == subsession_id

    def test_subsession_api_assigns_keynote_by_code(self, api_client, t_event_manager, t_event):
        """Test API workflow: create keynote, create subsession referencing keynote, verify assignment."""
        api_client.force_authenticate(user=t_event_manager)

        # 1. Create keynote and session
        session = SessionFactory(event=t_event)
        keynote = KeynoteFactory(event=t_event, code="KEYNOTE-002", session=None, subsession=None)

        # 2. Create subsession via API with program referencing keynote
        subsession_data = {
            "title": "Test Subsession",
            "program": "Welcome to our subsession.\n\n[keynote:KEYNOTE-002]\n\nThank you.",
        }
        response = api_client.post(reverse("v1:session-subsessions-list", args=[session.pk]), subsession_data)
        assert response.status_code == 201

        # 3. Check that keynote has been assigned to session and subsession
        keynote.refresh_from_db()
        subsession_id = response.data["id"]
        assert keynote.session_id == session.pk
        assert keynote.subsession_id == subsession_id

    def test_session_model_direct_save_assigns_paper(self, db, t_event):
        """Test model workflow: create paper, save session with program referencing paper, verify assignment."""
        # 1. Create paper
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        # 2. Create and save session with program referencing paper (no start/end times to avoid datetime issues)
        session = SessionFactory.build(event=t_event, program=f"[paper:{paper.pk}]", start_at=None, end_at=None)
        session.full_clean()  # This should trigger assignment
        session.save()

        # 3. Check that paper has been assigned to session
        paper.refresh_from_db()
        assert paper.session == session
        assert paper.subsession is None

    def test_session_model_direct_save_assigns_keynote(self, db, t_event):
        """Test model workflow: create keynote, save session with program referencing keynote, verify assignment."""
        # 1. Create keynote
        keynote = KeynoteFactory(event=t_event, code="KEYNOTE-003", session=None, subsession=None)

        # 2. Create and save session with program referencing keynote (no start/end times to avoid datetime issues)
        session = SessionFactory.build(event=t_event, program="[keynote:KEYNOTE-003]", start_at=None, end_at=None)
        session.full_clean()  # This should trigger assignment
        session.save()

        # 3. Check that keynote has been assigned to session
        keynote.refresh_from_db()
        assert keynote.session == session
        assert keynote.subsession is None

    def test_subsession_model_direct_save_assigns_paper(self, db, t_event):
        """Test model workflow: create paper, save subsession with program referencing paper, verify assignment."""
        # 1. Create paper and session (session must be saved for subsessions)
        session = SessionFactory(event=t_event, start_at=None, end_at=None)
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        # 2. Create and save subsession with program referencing paper
        subsession = SubsessionFactory.build(session=session, program=f"[paper:{paper.pk}]")
        subsession.full_clean()  # This should trigger assignment
        subsession.save()

        # 3. Check that paper has been assigned to session and subsession
        paper.refresh_from_db()
        assert paper.session == session
        assert paper.subsession == subsession

    def test_cross_assignment_validation_fails(self, db, t_event):
        """Test that papers/keynotes cannot be assigned to multiple sessions."""
        # 1. Create paper and assign to first session (no start/end times to avoid datetime issues)
        session1 = SessionFactory(event=t_event, start_at=None, end_at=None)
        paper = PaperFactory(event=t_event, session=session1, subsession=None)

        # 2. Try to create second session referencing the same paper
        session2 = SessionFactory.build(event=t_event, program=f"[paper:{paper.pk}]", start_at=None, end_at=None)

        # 3. Should fail validation
        with pytest.raises(ValidationError) as exc_info:
            session2.full_clean()

        assert "already assigned" in str(exc_info.value)

    def test_nonexistent_reference_validation_fails(self, db, t_event):
        """Test that references to nonexistent papers/keynotes fail validation."""
        # Create session with references to nonexistent items (no start/end times to avoid datetime issues)
        session = SessionFactory.build(
            event=t_event, program="[paper:99999] and [keynote:NONEXISTENT]", start_at=None, end_at=None
        )

        # Should fail validation
        with pytest.raises(ValidationError) as exc_info:
            session.full_clean()

        error_str = str(exc_info.value)
        assert "99999" in error_str or "NONEXISTENT" in error_str

    def test_multiple_references_in_single_program(self, db, t_event):
        """Test that multiple paper/keynote references in one program work correctly."""
        # 1. Create papers and keynotes
        paper1 = PaperFactory(event=t_event, session=None, subsession=None)
        paper2 = PaperFactory(event=t_event, session=None, subsession=None, extra_data={"internal_id": "P002"})
        keynote1 = KeynoteFactory(event=t_event, code="KN001", session=None, subsession=None)
        keynote2 = KeynoteFactory(event=t_event, code="KN002", session=None, subsession=None)

        # 2. Create session with multiple references
        program = f"""
        Welcome to our conference!

        First we have [keynote:KN001]
        Then we have [paper:{paper1.pk}]
        Followed by [paperi:P002]
        And finally [keynote:KN002]
        """

        session = SessionFactory.build(event=t_event, program=program, start_at=None, end_at=None)
        session.full_clean()
        session.save()

        # 3. Check all items are assigned
        paper1.refresh_from_db()
        paper2.refresh_from_db()
        keynote1.refresh_from_db()
        keynote2.refresh_from_db()

        assert paper1.session == session
        assert paper2.session == session
        assert keynote1.session == session
        assert keynote2.session == session
