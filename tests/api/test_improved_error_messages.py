"""
Test for improved error messages in program assignment conflicts.
"""

import pytest
from django.core.exceptions import ValidationError

from evan.utils.factories import KeynoteFactory, PaperFactory, SessionFactory, SubsessionFactory


@pytest.mark.api
class TestImprovedErrorMessages:
    """Test that error messages are clear and informative."""

    def test_paper_cross_subsession_error_message_with_internal_id(self, db, t_event):
        """Test error message format when paper with internal ID conflicts between subsessions."""

        session = SessionFactory(event=t_event, code="ML")
        subsession_a = SubsessionFactory(session=session, title="Machine Learning Basics", order=1)
        subsession_b = SubsessionFactory(session=session, title="Advanced ML", order=2)

        paper = PaperFactory(
            event=t_event, session=session, subsession=subsession_a, extra_data={"internal_id": "ML_001"}
        )

        subsession_b.program = f"[paper:{paper.pk}]"

        with pytest.raises(ValidationError) as exc_info:
            subsession_b.save()

        error_message = str(exc_info.value)

        assert f"Paper {paper.pk} (internal ML_001)" in error_message
        assert "'Machine Learning Basics', which is ML I" in error_message
        assert "'Advanced ML', which is ML II" in error_message

    def test_paper_cross_subsession_error_message_without_internal_id(self, db, t_event):
        """Test error message format when paper without internal ID conflicts between subsessions."""

        session = SessionFactory(event=t_event, code="AI")
        subsession_a = SubsessionFactory(session=session, title="", order=1)  # No title
        subsession_b = SubsessionFactory(session=session, title="Neural Networks", order=2)

        paper = PaperFactory(
            event=t_event,
            session=session,
            subsession=subsession_a,
            # No internal_id in extra_data
        )

        subsession_b.program = f"[paper:{paper.pk}]"

        with pytest.raises(ValidationError) as exc_info:
            subsession_b.save()

        error_message = str(exc_info.value)

        assert f"Paper {paper.pk}" in error_message
        assert "(internal" not in error_message  # Should not mention internal ID
        assert "'AI I'" in error_message  # Subsession without title shows as code + roman
        assert "'Neural Networks', which is AI II" in error_message

    def test_keynote_cross_subsession_error_message(self, db, t_event):
        """Test error message format when keynote conflicts between subsessions."""

        session = SessionFactory(event=t_event, code="CONF")
        subsession_a = SubsessionFactory(session=session, title="Opening", order=1)
        subsession_b = SubsessionFactory(session=session, title="Closing", order=2)

        KeynoteFactory(event=t_event, code="KEYNOTE_001", session=session, subsession=subsession_a)

        subsession_b.program = "[keynote:KEYNOTE_001]"

        with pytest.raises(ValidationError) as exc_info:
            subsession_b.save()

        error_message = str(exc_info.value)

        assert "Keynote KEYNOTE_001" in error_message
        assert "'Opening', which is CONF I" in error_message
        assert "'Closing', which is CONF II" in error_message

    def test_high_order_subsession_roman_numerals(self, db, t_event):
        """Test that high-order subsessions (>10) fall back to numbers."""

        session = SessionFactory(event=t_event, code="WORKSHOP")
        subsession_a = SubsessionFactory(session=session, title="Session A", order=11)
        subsession_b = SubsessionFactory(session=session, title="Session B", order=15)

        paper = PaperFactory(event=t_event, session=session, subsession=subsession_a)

        subsession_b.program = f"[paper:{paper.pk}]"

        with pytest.raises(ValidationError) as exc_info:
            subsession_b.save()

        error_message = str(exc_info.value)

        assert "'Session A', which is WORKSHOP 11" in error_message
        assert "'Session B', which is WORKSHOP 15" in error_message
