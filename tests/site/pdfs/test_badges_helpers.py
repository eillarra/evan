"""Tests for pure helper functions and sort/group logic in evan.site.pdfs.badges.

The reportlab Drawing construction in draw_badge is heavy layout code and is
not tested here; we cover the pure helpers and the importlib boundary.
"""

from unittest.mock import MagicMock, patch

import pytest

from evan.site.pdfs.badges import get_custom_icons, get_font_size


class TestGetFontSize:
    """get_font_size scales the font down when text exceeds the char budget."""

    def test_returns_max_size_when_text_fits(self):
        """Short text returns the max size unchanged."""
        assert get_font_size("short", max_size=26.0, char_max=17) == 26.0

    def test_scales_down_when_text_too_long(self):
        """Text longer than char_max is scaled proportionally."""
        long_text = "a" * 34  # double the char_max
        result = get_font_size(long_text, max_size=26.0, char_max=17)

        assert result == pytest.approx(13.0)

    def test_exact_boundary_returns_max_size(self):
        """Text exactly at char_max still returns the max size."""
        text = "a" * 17
        assert get_font_size(text, max_size=26.0, char_max=17) == 26.0


class TestGetCustomIcons:
    """get_custom_icons imports an event-specific module at the boundary."""

    def test_returns_empty_when_no_custom_module(self):
        """An unknown event code yields no custom icons."""
        result = get_custom_icons("no-such-event", MagicMock())

        assert result == []

    def test_returns_custom_info_when_module_exists(self):
        """When a custom module exposes get_custom_info, its result is returned."""
        fake_module = MagicMock()
        fake_module.get_custom_info.return_value = [{"filename": "icon.png"}]

        with patch("evan.site.pdfs.badges.importlib.import_module", return_value=fake_module):
            result = get_custom_icons("my-event", MagicMock())

        assert result == [{"filename": "icon.png"}]

    def test_returns_empty_when_module_has_no_get_custom_info(self):
        """A custom module without get_custom_info yields no icons."""
        fake_module = MagicMock(spec=[])  # no attributes

        with patch("evan.site.pdfs.badges.importlib.import_module", return_value=fake_module):
            result = get_custom_icons("my-event", MagicMock())

        assert result == []

    def test_forwards_person_data_to_custom_info(self):
        """person_data is forwarded to the custom info function."""
        fake_module = MagicMock()
        fake_module.get_custom_info.return_value = []
        registration = MagicMock()
        person_data = {"name": "Guest"}

        with patch("evan.site.pdfs.badges.importlib.import_module", return_value=fake_module) as mock_import:
            get_custom_icons("my-event", registration, person_data)

        fake_module.get_custom_info.assert_called_once_with(registration, person_data)
        mock_import.assert_called_once_with("evan.site.pdfs.custom.my-event")
