"""
Test for subsession assignment cleanup functionality.

Tests the new behavior where papers/keynotes are automatically unassigned from
subsessions when their references are removed from program templates.
"""

import pytest

from tests._factories import KeynoteFactory, PaperFactory, SessionFactory, SubsessionFactory


@pytest.mark.api
class TestSubsessionAssignmentCleanup:
    """Test automatic cleanup of orphaned subsession assignments."""

    def test_paper_unassigned_from_subsession_when_reference_removed(self, db, t_event):
        """Test that papers are unassigned from subsession when removed from program."""
        # Setup: Create session, subsession, and paper
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session, program="")
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        # Step 1: Add paper reference to program (should assign paper)
        subsession.program = f"[paper:{paper.pk}]"
        subsession.save()

        # Verify paper is assigned to both session and subsession
        paper.refresh_from_db()
        assert paper.session == session
        assert paper.subsession == subsession

        # Step 2: Remove paper reference from program (should unassign from subsession)
        subsession.program = "Some other content without paper reference"
        subsession.save()

        # Verify paper is unassigned from subsession but keeps session assignment
        paper.refresh_from_db()
        assert paper.session == session  # Session assignment preserved
        assert paper.subsession is None  # Subsession assignment removed

    def test_keynote_unassigned_from_subsession_when_reference_removed(self, db, t_event):
        """Test that keynotes are unassigned from subsession when removed from program."""
        # Setup: Create session, subsession, and keynote
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session, program="")
        keynote = KeynoteFactory(event=t_event, code="KN001", session=None, subsession=None)

        # Step 1: Add keynote reference to program (should assign keynote)
        subsession.program = "[keynote:KN001]"
        subsession.save()

        # Verify keynote is assigned to both session and subsession
        keynote.refresh_from_db()
        assert keynote.session == session
        assert keynote.subsession == subsession

        # Step 2: Remove keynote reference from program (should unassign from subsession)
        subsession.program = "Some other content without keynote reference"
        subsession.save()

        # Verify keynote is unassigned from subsession but keeps session assignment
        keynote.refresh_from_db()
        assert keynote.session == session  # Session assignment preserved
        assert keynote.subsession is None  # Subsession assignment removed

    def test_multiple_papers_cleanup_selectively(self, db, t_event):
        """Test that only unreferenced papers are unassigned, referenced ones remain."""
        # Setup: Create session, subsession, and multiple papers
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session, program="")
        paper1 = PaperFactory(event=t_event, session=None, subsession=None)
        paper2 = PaperFactory(event=t_event, session=None, subsession=None)
        paper3 = PaperFactory(event=t_event, session=None, subsession=None)

        # Step 1: Add all papers to program (should assign all)
        subsession.program = f"[paper:{paper1.pk}] [paper:{paper2.pk}] [paper:{paper3.pk}]"
        subsession.save()

        # Verify all papers are assigned
        for paper in [paper1, paper2, paper3]:
            paper.refresh_from_db()
            assert paper.session == session
            assert paper.subsession == subsession

        # Step 2: Remove only paper2 from program (should unassign only paper2)
        subsession.program = f"[paper:{paper1.pk}] [paper:{paper3.pk}]"
        subsession.save()

        # Verify selective cleanup
        paper1.refresh_from_db()
        paper2.refresh_from_db()
        paper3.refresh_from_db()

        # paper1 and paper3 should remain assigned
        assert paper1.subsession == subsession
        assert paper3.subsession == subsession

        # paper2 should be unassigned from subsession but keep session
        assert paper2.session == session
        assert paper2.subsession is None

    def test_paper_can_be_reassigned_after_cleanup(self, db, t_event):
        """Test that cleaned up papers can be assigned to other subsessions."""
        # Setup: Create session with two subsessions and a paper
        session = SessionFactory(event=t_event)
        subsession_a = SubsessionFactory(session=session, title="Subsession A", order=1, program="")
        subsession_b = SubsessionFactory(session=session, title="Subsession B", order=2, program="")
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        # Step 1: Assign paper to subsession A
        subsession_a.program = f"[paper:{paper.pk}]"
        subsession_a.save()

        paper.refresh_from_db()
        assert paper.subsession == subsession_a

        # Step 2: Remove paper from subsession A (should cleanup assignment)
        subsession_a.program = "No papers here"
        subsession_a.save()

        paper.refresh_from_db()
        assert paper.subsession is None

        # Step 3: Should now be able to assign to subsession B without validation error
        subsession_b.program = f"[paper:{paper.pk}]"
        subsession_b.save()  # Should not raise ValidationError

        paper.refresh_from_db()
        assert paper.subsession == subsession_b

    def test_internal_id_paper_cleanup(self, db, t_event):
        """Test cleanup works with internal ID references."""
        # Setup: Create session, subsession, and paper with internal ID
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session, program="")
        paper = PaperFactory(event=t_event, session=None, subsession=None, extra_data={"internal_id": "PAPER_001"})

        # Step 1: Add paper by internal ID (should assign)
        subsession.program = "[paperi:PAPER_001]"
        subsession.save()

        paper.refresh_from_db()
        assert paper.subsession == subsession

        # Step 2: Remove internal ID reference (should cleanup)
        subsession.program = "No papers referenced here"
        subsession.save()

        paper.refresh_from_db()
        assert paper.subsession is None

    def test_empty_program_cleans_up_all_assignments(self, db, t_event):
        """Test that clearing program entirely cleans up all assignments."""
        # Setup: Create session, subsession with multiple items
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session, program="")
        paper = PaperFactory(event=t_event, session=None, subsession=None)
        keynote = KeynoteFactory(event=t_event, code="KN001", session=None, subsession=None)

        # Step 1: Assign both items
        subsession.program = f"[paper:{paper.pk}] [keynote:KN001]"
        subsession.save()

        paper.refresh_from_db()
        keynote.refresh_from_db()
        assert paper.subsession == subsession
        assert keynote.subsession == subsession

        # Step 2: Clear program entirely
        subsession.program = ""
        subsession.save()

        # Verify both items are cleaned up
        paper.refresh_from_db()
        keynote.refresh_from_db()
        assert paper.subsession is None
        assert keynote.subsession is None

    def test_session_assignments_not_affected_by_subsession_cleanup(self, db, t_event):
        """Test that session-level assignments are not affected by subsession cleanup."""
        # Setup: Create session with paper assigned directly to session
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session, program="")
        paper = PaperFactory(event=t_event, session=session, subsession=None)

        # Step 1: Add paper to subsession program
        subsession.program = f"[paper:{paper.pk}]"
        subsession.save()

        paper.refresh_from_db()
        assert paper.subsession == subsession

        # Step 2: Remove from subsession program
        subsession.program = ""
        subsession.save()

        # Verify paper keeps session assignment but loses subsession
        paper.refresh_from_db()
        assert paper.session == session  # Should remain
        assert paper.subsession is None  # Should be cleaned up
