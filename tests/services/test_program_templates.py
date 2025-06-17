import pytest

from evan.models import Paper, Session
from evan.utils.program_templates import program_processor


@pytest.fixture
def session(t_event):
    return Session.objects.create(event=t_event, title="Test Session", program="", extra_data={})


@pytest.fixture
def paper_with_numeric_internal_id(t_event, session):
    return Paper.objects.create(
        event=t_event,
        session=session,
        title="Paper with Numeric Internal ID",
        extra_data={"internal_id": 42, "authors_str": "John Doe, Jane Smith"},
    )


@pytest.fixture
def paper_with_string_internal_id(t_event, session):
    return Paper.objects.create(
        event=t_event,
        session=session,
        title="Paper with String Internal ID",
        extra_data={"internal_id": "ABC123", "authors_str": "Alice Cooper"},
    )


@pytest.fixture
def paper_without_internal_id(t_event, session):
    return Paper.objects.create(event=t_event, session=session, title="Paper without Internal ID", extra_data={})


@pytest.mark.django_db
class TestProgramTemplateProcessor:
    def test_extract_paper_database_id_references(self, paper_without_internal_id):
        template = f"First paper: [paper:{paper_without_internal_id.pk}]"
        paper_ids = program_processor.extract_paper_references(template)
        assert paper_ids == [paper_without_internal_id.pk]

    def test_extract_paper_internal_id_references_numeric(self, paper_with_numeric_internal_id):
        template = "[paperi:42]"
        paper_ids = program_processor.extract_paper_references(template)
        assert paper_ids == [paper_with_numeric_internal_id.pk]

    def test_extract_paper_internal_id_references_string(self, paper_with_string_internal_id):
        template = "[paperi:ABC123]"
        paper_ids = program_processor.extract_paper_references(template)
        assert paper_ids == [paper_with_string_internal_id.pk]

    def test_extract_mixed_paper_references(
        self, paper_without_internal_id, paper_with_numeric_internal_id, paper_with_string_internal_id
    ):
        template = f"""
        Database ID: [paper:{paper_without_internal_id.pk}]
        Numeric internal: [paperi:42]
        String internal: [paperi:ABC123]
        """
        paper_ids = program_processor.extract_paper_references(template)
        expected_ids = [
            paper_without_internal_id.pk,
            paper_with_numeric_internal_id.pk,
            paper_with_string_internal_id.pk,
        ]
        assert sorted(paper_ids) == sorted(expected_ids)

    def test_extract_nonexistent_internal_id(self):
        template = "[paperi:NONEXISTENT]"
        paper_ids = program_processor.extract_paper_references(template)
        assert paper_ids == []

    def test_process_template_with_database_id(self, t_event):
        # Create session and paper directly in the test for better isolation
        from evan.models import Session
        from evan.utils.program_templates import ProgramTemplateProcessor

        session = Session.objects.create(event=t_event, title="Isolated Test Session", program="", extra_data={})
        paper = Paper.objects.create(event=t_event, session=session, title="Paper without Internal ID", extra_data={})

        # Use a fresh processor instance to avoid caching issues
        fresh_processor = ProgramTemplateProcessor()
        template = f"Paper: [paper:{paper.pk}]"
        result = fresh_processor.process_template(template, t_event.pk)
        assert "Paper without Internal ID" in result

    def test_process_template_with_numeric_internal_id(self, t_event, paper_with_numeric_internal_id):
        template = "[paperi:42]"
        result = program_processor.process_template(template, t_event.pk)
        assert "Paper with Numeric Internal ID" in result
        assert "John Doe, Jane Smith" in result

    def test_process_template_with_string_internal_id(self, t_event, paper_with_string_internal_id):
        template = "[paperi:ABC123]"
        result = program_processor.process_template(template, t_event.pk)
        assert "Paper with String Internal ID" in result
        assert "Alice Cooper" in result

    def test_process_template_with_nonexistent_internal_id(self, t_event):
        template = "[paperi:NONEXISTENT]"
        result = program_processor.process_template(template, t_event.pk)
        assert "[Paper iNONEXISTENT not found]" in result

    def test_validate_template_with_valid_references(
        self, t_event, paper_without_internal_id, paper_with_numeric_internal_id
    ):
        template = f"[paper:{paper_without_internal_id.pk}] and [paperi:42]"
        validation = program_processor.validate_template(template, t_event.pk)
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
        expected_paper_ids = [paper_without_internal_id.pk, paper_with_numeric_internal_id.pk]
        assert sorted(validation["paper_references"]) == sorted(expected_paper_ids)

    def test_validate_template_with_invalid_database_id(self, t_event):
        template = "[paper:99999]"
        validation = program_processor.validate_template(template, t_event.pk)
        assert validation["is_valid"] is False
        assert "Paper 99999 not found" in validation["errors"]

    def test_validate_template_with_invalid_internal_id(self, t_event):
        template = "[paperi:INVALID]"
        validation = program_processor.validate_template(template, t_event.pk)
        assert validation["is_valid"] is True
        assert len(validation["paper_references"]) == 0

    def test_paper_reference_deduplication(self, paper_without_internal_id):
        template = f"[paper:{paper_without_internal_id.pk}] [paper:{paper_without_internal_id.pk}]"
        paper_ids = program_processor.extract_paper_references(template)
        assert paper_ids == [paper_without_internal_id.pk]

    def test_internal_id_stored_as_integer_vs_string(self, t_event, session):
        paper_int_stored_as_string = Paper.objects.create(
            event=t_event, session=session, title="Paper with Int as String", extra_data={"internal_id": "123"}
        )

        template_int = "[paperi:123]"
        paper_ids = program_processor.extract_paper_references(template_int)
        assert paper_ids == [paper_int_stored_as_string.pk]

    def test_empty_template_handling(self, t_event):
        paper_ids = program_processor.extract_paper_references("")
        assert paper_ids == []

        result = program_processor.process_template("", t_event.pk)
        assert result == ""

        validation = program_processor.validate_template("", t_event.pk)
        assert validation["is_valid"] is True
