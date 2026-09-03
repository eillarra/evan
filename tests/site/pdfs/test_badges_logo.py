"""Tests for the event logo resolution used by badge PDF generation.

The badge PDF renders the event's SVG logo file (a public file tagged
``logo``) as a vector drawing. These tests cover the model helper and the
PDF-module loader; drawing itself is layout code and not tested here.
"""

import pytest
from django.core.files.base import ContentFile
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import black

from evan.models import File
from evan.site.pdfs.badges import (
    BADGE_WIDTH,
    LOGO_Y,
    draw_badge,
    get_event_logo_drawing,
)


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>'


@pytest.fixture
def media_root(settings, tmp_path) -> None:
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def logo_event(t_event):
    """Return a creation helper attaching files to the event."""

    def _create_logo(filename: str, content: bytes = SVG, tags: list | None = None, type_: str = File.PUBLIC):
        return File.objects.create(
            content_object=t_event,
            type=type_,
            file=ContentFile(content, name=filename),
            tags=tags if tags is not None else ["logo"],
        )

    return _create_logo


class TestEventGetLogoFile:
    """Event.get_logo_file returns only public SVG files tagged logo."""

    def test_returns_svg_logo(self, media_root, logo_event, t_event) -> None:
        """An SVG file tagged logo is returned."""
        logo_event("logo.svg")

        assert t_event.get_logo_file() is not None

    def test_returns_none_without_logo(self, media_root, t_event) -> None:
        """An event without logo files has no logo."""
        assert t_event.get_logo_file() is None

    def test_ignores_non_svg_files(self, media_root, logo_event, t_event) -> None:
        """Tagged files other than SVG are skipped."""
        logo_event("logo.png", content=b"not really an svg")

        assert t_event.get_logo_file() is None

    def test_ignores_private_files(self, media_root, logo_event, t_event) -> None:
        """Private files tagged logo are ignored."""
        logo_event("logo.svg", type_=File.PRIVATE)

        assert t_event.get_logo_file() is None

    def test_ignores_other_tags(self, media_root, logo_event, t_event) -> None:
        """Files without the logo tag are ignored, even when SVG."""
        logo_event("avatar.svg", tags=["avatar"])

        assert t_event.get_logo_file() is None


class TestGetEventLogoDrawing:
    """get_event_logo_drawing parses the event logo into a reportlab drawing."""

    def test_parses_svg_logo(self, media_root, logo_event, t_event) -> None:
        """A valid SVG logo becomes a drawing with positive dimensions."""
        logo_event("logo.svg")

        drawing = get_event_logo_drawing(t_event)

        assert drawing is not None
        assert drawing.width > 0
        assert drawing.height > 0

    def test_returns_none_without_logo(self, media_root, t_event) -> None:
        """No logo file means no drawing."""
        assert get_event_logo_drawing(t_event) is None

    def test_returns_none_for_corrupt_svg(self, media_root, logo_event, t_event) -> None:
        """Invalid SVG content is skipped instead of crashing badge generation."""
        logo_event("logo.svg", content=b"<!this is not svg><broken>")

        assert get_event_logo_drawing(t_event) is None


class TestDrawBadgeLogo:
    """draw_badge places the logo on the first (left) badge half only."""

    @pytest.fixture
    def logo_drawing(self) -> Drawing:
        return Drawing(10, 10)

    def test_logo_only_on_first_half(self, logo_drawing: Drawing) -> None:
        """The logo is drawn once, on the left half, below the attendee name."""
        badge = draw_badge(
            event_name="Event",
            event_hashtag="ev",
            event_info="info",
            attendee_name="Jane Doe",
            color=black,
            logo=logo_drawing,
        )

        logos = [item for item in badge.contents if isinstance(item, Drawing)]

        assert len(logos) == 1
        (logo,) = logos
        assert logo.transform[4] < BADGE_WIDTH / 2
        assert logo.transform[5] == LOGO_Y

    def test_no_logo_when_disabled(self, logo_drawing: Drawing) -> None:
        """No logo drawing is added when no logo is passed."""
        badge = draw_badge(
            event_name="Event",
            event_hashtag="ev",
            event_info="info",
            attendee_name="Jane Doe",
            color=black,
        )

        assert not [item for item in badge.contents if isinstance(item, Drawing)]
