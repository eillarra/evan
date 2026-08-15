"""Tests for the program template service.

Covers reference extraction, template validation, paper/keynote sync, and
orphan cleanup. Tests assert real model state changes, not internal calls.
"""

import pytest
from django.core.exceptions import ValidationError

from evan.services.program import ProgramService
from tests._factories import (
    EventFactory,
    KeynoteFactory,
    PaperFactory,
    SessionFactory,
    SubsessionFactory,
)


@pytest.fixture
def service():
    return ProgramService()


# ---------------------------------------------------------------------------
# extract_paper_references
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExtractPaperReferences:
    """extract_paper_references turns [paper:N] and [paperi:ID] tokens into DB IDs."""

    def test_db_id_pattern(self, service, t_event) -> None:
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        result = service.extract_paper_references(f"[paper:{paper.id}]")

        assert result == [paper.id]

    def test_internal_id_pattern_with_string_lookup(self, service, t_event) -> None:
        paper = PaperFactory(event=t_event, session=None, subsession=None, extra_data={"internal_id": "ABC-001"})

        result = service.extract_paper_references("[paperi:ABC-001]")

        assert result == [paper.id]

    def test_internal_id_pattern_with_int_lookup(self, service, t_event) -> None:
        paper = PaperFactory(event=t_event, session=None, subsession=None, extra_data={"internal_id": 42})

        result = service.extract_paper_references("[paperi:42]")

        assert result == [paper.id]

    def test_mixed_references_deduplicated(self, service, t_event) -> None:
        paper = PaperFactory(event=t_event, session=None, subsession=None, extra_data={"internal_id": "X1"})

        result = service.extract_paper_references(f"[paper:{paper.id}] [paperi:X1] [paper:{paper.id}]")

        assert result == [paper.id]

    def test_nonexistent_internal_id_is_gracefully_skipped(self, service) -> None:
        assert service.extract_paper_references("[paperi:NOPE]") == []

    def test_empty_template_returns_empty_list(self, service) -> None:
        assert service.extract_paper_references("") == []

    def test_none_template_returns_empty_list(self, service) -> None:
        assert service.extract_paper_references(None) == []


# ---------------------------------------------------------------------------
# extract_keynote_references
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExtractKeynoteReferences:
    """extract_keynote_references turns [keynote:CODE] tokens into deduplicated codes."""

    def test_single_code(self, service) -> None:
        assert service.extract_keynote_references("[keynote:KN01]") == ["KN01"]

    def test_multiple_codes_deduplicated(self, service) -> None:
        result = service.extract_keynote_references("[keynote:KN01] [keynote:KN02] [keynote:KN01]")
        assert sorted(result) == ["KN01", "KN02"]

    def test_empty_template_returns_empty_list(self, service) -> None:
        assert service.extract_keynote_references("") == []

    def test_none_template_returns_empty_list(self, service) -> None:
        assert service.extract_keynote_references(None) == []


# ---------------------------------------------------------------------------
# validate_template
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateTemplate:
    """validate_template reports errors for nonexistent or out-of-event references."""

    def test_all_valid_references(self, service, t_event) -> None:
        paper = PaperFactory(event=t_event, session=None, subsession=None)
        keynote = KeynoteFactory(event=t_event)

        result = service.validate_template(f"[paper:{paper.id}] [keynote:{keynote.code}]", event_id=t_event.id)

        assert result["is_valid"] is True
        assert result["errors"] == []
        assert paper.id in result["paper_references"]
        assert keynote.code in result["keynote_references"]

    def test_nonexistent_paper_id(self, service, t_event) -> None:
        result = service.validate_template("[paper:999999]", event_id=t_event.id)

        assert result["is_valid"] is False
        assert any("999999" in e for e in result["errors"])

    def test_nonexistent_keynote_code(self, service, t_event) -> None:
        result = service.validate_template("[keynote:NOPE]", event_id=t_event.id)

        assert result["is_valid"] is False
        assert any("NOPE" in e for e in result["errors"])

    def test_empty_template_is_valid(self, service) -> None:
        result = service.validate_template("")

        assert result["is_valid"] is True
        assert result["paper_references"] == []
        assert result["keynote_references"] == []

    def test_whitespace_only_template_is_valid(self, service) -> None:
        result = service.validate_template("   \n\t  ")

        assert result["is_valid"] is True

    def test_paper_from_different_event_is_rejected(self, service, t_event) -> None:
        other_event = EventFactory()
        paper = PaperFactory(event=other_event, session=None, subsession=None)

        result = service.validate_template(f"[paper:{paper.id}]", event_id=t_event.id)

        assert result["is_valid"] is False


# ---------------------------------------------------------------------------
# validate_and_sync_program_papers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateAndSyncProgramPapers:
    """Sync assigns unassigned papers and rejects cross-session/subsession conflicts."""

    def test_unassigned_paper_referenced_by_session_program(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        service.validate_and_sync_program_papers(f"[paper:{paper.id}]", session)

        paper.refresh_from_db()
        assert paper.session == session
        assert paper.subsession is None

    def test_unassigned_paper_referenced_by_subsession_program(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=None, subsession=None)

        service.validate_and_sync_program_papers(f"[paper:{paper.id}]", session, subsession_obj=subsession)

        paper.refresh_from_db()
        assert paper.session == session
        assert paper.subsession == subsession

    def test_paper_in_same_session_no_subsession_referenced_by_subsession(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=None)

        service.validate_and_sync_program_papers(f"[paper:{paper.id}]", session, subsession_obj=subsession)

        paper.refresh_from_db()
        assert paper.subsession == subsession

    def test_paper_already_in_different_session_is_rejected(self, service, t_event) -> None:
        session_a = SessionFactory(event=t_event)
        session_b = SessionFactory(event=t_event)
        paper = PaperFactory(event=t_event, session=session_a, subsession=None)

        with pytest.raises(ValidationError, match="already assigned to session"):
            service.validate_and_sync_program_papers(f"[paper:{paper.id}]", session_b)

    def test_paper_already_in_different_subsession_is_rejected(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        sub_a = SubsessionFactory(session=session)
        sub_b = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=sub_a)

        with pytest.raises(ValidationError, match="already assigned to subsession"):
            service.validate_and_sync_program_papers(f"[paper:{paper.id}]", session, subsession_obj=sub_b)

    def test_nonexistent_paper_id_raises_validation_error(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)

        with pytest.raises(ValidationError, match="not found"):
            service.validate_and_sync_program_papers("[paper:999999]", session)

    def test_empty_program_with_subsession_triggers_cleanup(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=subsession)

        service.validate_and_sync_program_papers("", session, subsession_obj=subsession)

        paper.refresh_from_db()
        assert paper.subsession is None
        assert paper.session == session  # session preserved


# ---------------------------------------------------------------------------
# validate_and_sync_program_keynotes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateAndSyncProgramKeynotes:
    """Keynote sync mirrors paper sync: assign, reject cross-session/subsession, cleanup."""

    def test_unassigned_keynote_referenced_by_session_program(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        keynote = KeynoteFactory(event=t_event, session=None, subsession=None)

        service.validate_and_sync_program_keynotes(f"[keynote:{keynote.code}]", session)

        keynote.refresh_from_db()
        assert keynote.session == session
        assert keynote.subsession is None

    def test_unassigned_keynote_referenced_by_subsession_program(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=None, subsession=None)

        service.validate_and_sync_program_keynotes(f"[keynote:{keynote.code}]", session, subsession_obj=subsession)

        keynote.refresh_from_db()
        assert keynote.session == session
        assert keynote.subsession == subsession

    def test_keynote_in_same_session_no_subsession_referenced_by_subsession(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=None)

        service.validate_and_sync_program_keynotes(f"[keynote:{keynote.code}]", session, subsession_obj=subsession)

        keynote.refresh_from_db()
        assert keynote.subsession == subsession

    def test_keynote_already_in_different_session_is_rejected(self, service, t_event) -> None:
        session_a = SessionFactory(event=t_event)
        session_b = SessionFactory(event=t_event)
        keynote = KeynoteFactory(event=t_event, session=session_a, subsession=None)

        with pytest.raises(ValidationError, match="already assigned to session"):
            service.validate_and_sync_program_keynotes(f"[keynote:{keynote.code}]", session_b)

    def test_keynote_already_in_different_subsession_is_rejected(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        sub_a = SubsessionFactory(session=session)
        sub_b = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=sub_a)

        with pytest.raises(ValidationError, match="already assigned to subsession"):
            service.validate_and_sync_program_keynotes(f"[keynote:{keynote.code}]", session, subsession_obj=sub_b)

    def test_nonexistent_keynote_code_raises_validation_error(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)

        with pytest.raises(ValidationError, match="not found"):
            service.validate_and_sync_program_keynotes("[keynote:NOPE]", session)

    def test_empty_program_with_subsession_triggers_cleanup(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=subsession)

        service.validate_and_sync_program_keynotes("", session, subsession_obj=subsession)

        keynote.refresh_from_db()
        assert keynote.subsession is None
        assert keynote.session == session


# ---------------------------------------------------------------------------
# cleanup_orphaned_subsession_paper_assignments
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCleanupOrphanedSubsessionPaperAssignments:
    """Removing a paper reference from a subsession program clears its subsession, keeps session."""

    def test_orphaned_paper_subsession_cleared_session_preserved(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=subsession)

        service.cleanup_orphaned_subsession_paper_assignments("[paper:0]", subsession)

        paper.refresh_from_db()
        assert paper.subsession is None
        assert paper.session == session

    def test_still_referenced_paper_is_untouched(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=subsession)

        service.cleanup_orphaned_subsession_paper_assignments(f"[paper:{paper.id}]", subsession)

        paper.refresh_from_db()
        assert paper.subsession == subsession

    def test_no_subsession_obj_is_noop(self, service) -> None:
        service.cleanup_orphaned_subsession_paper_assignments("[paper:0]", None)  # no raise


# ---------------------------------------------------------------------------
# cleanup_orphaned_subsession_keynote_assignments
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCleanupOrphanedSubsessionKeynoteAssignments:
    """Removing a keynote reference from a subsession program clears its subsession, keeps session."""

    def test_orphaned_keynote_subsession_cleared_session_preserved(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=subsession)

        service.cleanup_orphaned_subsession_keynote_assignments("[keynote:0]", subsession)

        keynote.refresh_from_db()
        assert keynote.subsession is None
        assert keynote.session == session

    def test_still_referenced_keynote_is_untouched(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        subsession = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=subsession)

        service.cleanup_orphaned_subsession_keynote_assignments(f"[keynote:{keynote.code}]", subsession)

        keynote.refresh_from_db()
        assert keynote.subsession == subsession

    def test_no_subsession_obj_is_noop(self, service) -> None:
        service.cleanup_orphaned_subsession_keynote_assignments("[keynote:0]", None)  # no raise


# ---------------------------------------------------------------------------
# Description formatters (covered via error messages)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDescriptionFormatters:
    """Formatters produce human-readable descriptions in validation errors."""

    def test_paper_description_includes_internal_id(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        sub_a = SubsessionFactory(session=session)
        sub_b = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=sub_a, extra_data={"internal_id": "INT-9"})

        with pytest.raises(ValidationError, match="internal INT-9"):
            service.validate_and_sync_program_papers(f"[paper:{paper.id}]", session, subsession_obj=sub_b)

    def test_subsession_description_uses_title_and_roman_numeral(self, service, t_event) -> None:
        session = SessionFactory(event=t_event, code="S1")
        sub_a = SubsessionFactory(session=session, title="Morning Talks", order=1)
        sub_b = SubsessionFactory(session=session, title="Afternoon", order=2)
        paper = PaperFactory(event=t_event, session=session, subsession=sub_a)

        with pytest.raises(ValidationError, match="Morning Talks"):
            service.validate_and_sync_program_papers(f"[paper:{paper.id}]", session, subsession_obj=sub_b)

    def test_keynote_description_uses_code(self, service, t_event) -> None:
        session = SessionFactory(event=t_event)
        sub_a = SubsessionFactory(session=session)
        sub_b = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=sub_a, code="KN42")

        with pytest.raises(ValidationError, match="Keynote KN42"):
            service.validate_and_sync_program_keynotes(f"[keynote:{keynote.code}]", session, subsession_obj=sub_b)
