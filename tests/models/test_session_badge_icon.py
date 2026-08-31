"""Tests for badge icon configuration on sessions (``SessionExtraData.badge_icon``).

Event managers select a badge icon per social event session from a fixed
whitelist; invalid keys are rejected when the session is saved.
"""

import os

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from evan.models.documents.badges import AVAILABLE_BADGE_ICONS, ICON_FILES
from tests._factories import SessionFactory


class TestSessionBadgeIconValidation:
    """Session.save enforces the badge icon whitelist and normalizes empties."""

    def test_badge_icon_with_valid_key_is_kept(self, db) -> None:
        """A whitelisted icon key round-trips through save."""
        session = SessionFactory(is_social_event=True, extra_data={"badge_icon": "boat_trip"})

        session.refresh_from_db()
        assert session.extra_data["badge_icon"] == "boat_trip"

    def test_badge_icon_with_unknown_key_is_rejected(self, db) -> None:
        """An unknown icon key raises a ValidationError listing the whitelist."""
        with pytest.raises(ValidationError, match="Unknown badge icon 'not-an-icon'"):
            SessionFactory(extra_data={"badge_icon": "not-an-icon"})

    def test_empty_badge_icon_normalizes_to_none(self, db) -> None:
        """An empty string is treated as no icon configured."""
        session = SessionFactory(extra_data={"badge_icon": "  "})

        session.refresh_from_db()
        assert session.extra_data.get("badge_icon") is None

    def test_available_badge_icons_all_have_files(self) -> None:
        """Every icon key (plus the struck camera) maps to an existing Material SVG."""
        icons_dir = os.path.join(settings.SITE_ROOT, "static", "images", "icons")
        available_files = {name.removesuffix(".svg") for name in os.listdir(icons_dir) if name.endswith(".svg")}

        assert set(ICON_FILES) >= set(AVAILABLE_BADGE_ICONS)
        for icon_file in ICON_FILES.values():
            assert icon_file in available_files, f"'icons/{icon_file}.svg' is missing for a whitelisted icon key."
