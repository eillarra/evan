"""Tests for Excel worksheet naming helpers."""

from evan.services.excel import build_unique_worksheet_name


def test_build_unique_worksheet_name_truncates_to_31_chars() -> None:
    """Long worksheet names are truncated to Excel's 31-character limit."""
    name = "SOCIAL - Welcome reception at Castle of the Counts"

    result = build_unique_worksheet_name(name, set())

    assert len(result) <= 31


def test_build_unique_worksheet_name_strips_invalid_chars() -> None:
    """Invalid Excel worksheet characters are removed from worksheet names."""
    name = "SOCIAL: Q&A / Intro? [Main] * Session \\ Track"

    result = build_unique_worksheet_name(name, set())

    for invalid in "[]:*?/\\":
        assert invalid not in result


def test_build_unique_worksheet_name_generates_safe_unique_suffixes() -> None:
    """Duplicate worksheet names receive a numeric suffix within 31 characters."""
    used_names: set[str] = set()
    base_name = "SOCIAL - Welcome reception at Castle of the Counts"

    first = build_unique_worksheet_name(base_name, used_names)
    used_names.add(first)

    second = build_unique_worksheet_name(base_name, used_names)

    assert first != second
    assert len(second) <= 31
    assert second.endswith(" (2)")
