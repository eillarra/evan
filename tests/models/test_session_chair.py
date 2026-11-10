"""Tests for the programme chair in ``SessionExtraData``.

The chair is free-text presentation metadata for the public programme; it is
never resolved to a user and never affects registration or access.
"""

import pytest

from evan.models.documents.sessions import get_validated_session_extra_data
from tests._factories import SessionFactory


class TestSessionChairNormalization:
    """Blank chairs normalize to null; real chairs round-trip unchanged."""

    def test_chair_is_preserved(self) -> None:
        """A non-blank chair is kept as written."""
        validated = get_validated_session_extra_data({"chair": "Ada Example"})

        assert validated["chair"] == "Ada Example"

    @pytest.mark.parametrize("value", ["", "   ", "\n\t"])
    def test_blank_chair_is_null(self, value: str) -> None:
        """Empty and whitespace-only chairs become null."""
        validated = get_validated_session_extra_data({"chair": value})

        assert validated["chair"] is None

    def test_missing_chair_defaults_to_null(self) -> None:
        """Sessions without a chair keep a null value."""
        validated = get_validated_session_extra_data({})

        assert validated["chair"] is None

    def test_chair_survives_session_save(self, db) -> None:
        """Session.save validates and stores the chair."""
        session = SessionFactory(extra_data={"chair": "Grace Example"})

        session.refresh_from_db()
        assert session.extra_data["chair"] == "Grace Example"

    def test_whitespace_chair_is_null_after_save(self, db) -> None:
        """A whitespace-only chair is stored as null."""
        session = SessionFactory(extra_data={"chair": "  "})

        session.refresh_from_db()
        assert session.extra_data["chair"] is None
