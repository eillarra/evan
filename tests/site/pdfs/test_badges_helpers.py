"""Tests for pure helper functions in evan.site.pdfs.badges.

The reportlab Drawing construction in draw_badge is heavy layout code and is
not tested here; we cover the pure helpers (font sizing, MECARD builder) and
the config-driven icon lookup.
"""

from datetime import date, timedelta

import pytest

from evan.models import Registration, Session
from evan.site.pdfs.badges import (
    build_mecard,
    format_event_info,
    get_badge_icons,
    get_font_size,
    registration_allows_photos,
)
from tests._factories import RegistrationFactory, SessionFactory, UserFactory


class TestGetFontSize:
    """get_font_size scales the font down when the text exceeds its character budget."""

    def test_returns_max_size_when_text_fits(self) -> None:
        """Short text returns max size unchanged."""
        assert get_font_size("short", max_size=26.0, char_max=17) == 26.0

    def test_scales_down_when_text_too_long(self) -> None:
        """Text longer than char_max is scaled proportionally."""
        long_text = "a" * 34  # double char_max
        result = get_font_size(long_text, max_size=26.0, char_max=17)

        assert result == pytest.approx(13.0)

    def test_exact_boundary_returns_max_size(self) -> None:
        """Text exactly char_max still returns max size."""
        text = "a" * 17
        assert get_font_size(text, max_size=26.0, char_max=17) == 26.0


class TestFormatEventInfo:
    """format_event_info builds the footer line with month-first, yearless dates."""

    @pytest.mark.parametrize(
        ("start", "end", "expected_date_part"),
        [
            (
                date(2025, 8, 11),
                date(2025, 8, 14),
                "augustus 11-14",
            ),
            (
                date(2025, 8, 28),
                date(2025, 9, 1),
                "augustus 28 - september 1",
            ),
            (
                date(2025, 8, 11),
                date(2025, 8, 11),
                "augustus 11",
            ),
        ],
    )
    def test_date_part_variants(self, start, end, expected_date_part) -> None:
        """Same-month ranges collapse to Month D1-D2; other cases use full dates."""
        result = format_event_info(start_date=start, end_date=end, city="Ghent", country="Belgium")

        assert result == f"{expected_date_part}, Ghent, Belgium"


class TestBuildMecard:
    """build_mecard produces QR contact payloads with only the set fields."""

    def test_builds_name_org_email(self) -> None:
        """All three fields are encoded in MECARD order and terminated with ;;."""
        payload = build_mecard(name="Jane Doe", affiliation="Ghent University", email="jane@example.com")

        assert payload == "MECARD:N:Jane Doe;ORG:Ghent University;EMAIL:jane@example.com;;"

    def test_escapes_special_characters(self) -> None:
        """Backslash, semicolon, comma and colon in values are escaped."""
        payload = build_mecard(name="Doe;J.", affiliation="Uni, Dept: X", email="a\\b@example.com")

        assert payload == "MECARD:N:Doe\\;J.;ORG:Uni\\, Dept\\: X;EMAIL:a\\\\b@example.com;;"

    def test_omits_empty_fields(self) -> None:
        """Empty affiliation and email fields are left out of the payload."""
        payload = build_mecard(name="Jane Doe")

        assert payload == "MECARD:N:Jane Doe;;"


def make_registration(**extra_data):
    """An unsaved registration carrying the given extra_data (no DB needed)."""
    return Registration(extra_data=extra_data)


class TestRegistrationAllowsPhotos:
    """registration_allows_photos reads the photo consent from extra_data."""

    def test_defaults_to_allowing_photos(self) -> None:
        """No recorded preference means the plain camera icon is used."""
        assert registration_allows_photos(make_registration()) is True

    def test_allow_photo_sharing_false_means_opted_out(self) -> None:
        """Attendees who opted out of photography get the struck camera icon."""
        registration = make_registration(_internal={"allow_photo_sharing": False})

        assert registration_allows_photos(registration) is False

    def test_allow_photo_sharing_true(self) -> None:
        """Explicit consent keeps the plain camera icon."""
        registration = make_registration(_internal={"allow_photo_sharing": True})

        assert registration_allows_photos(registration) is True


def make_social_session(event, title: str, icon: str | None = None, *, start_at=None):
    """Create social event session with an optional badge icon and start time."""
    kwargs = {"start_at": start_at} if start_at is not None else {}
    return SessionFactory(
        event=event,
        title=title,
        is_social_event=True,
        extra_data={"badge_icon": icon} if icon else {},
        **kwargs,
    )


@pytest.mark.django_db
class TestGetBadgeIcons:
    """get_badge_icons reads validated badge icons from social event sessions."""

    def test_returns_empty_without_social_sessions(self, t_event) -> None:
        """A registration without sessions yields no icons."""
        registration = RegistrationFactory(event=t_event, user=UserFactory())

        assert get_badge_icons(registration) == []

    def test_ignores_social_sessions_without_icon(self, t_event) -> None:
        """Social event sessions without a configured icon contribute nothing."""
        SessionFactory(event=t_event, title="Pub quiz", is_social_event=True)
        registration = RegistrationFactory(event=t_event, user=UserFactory())
        registration.sessions.add(SessionFactory(event=t_event, title="Tour", is_social_event=True))

        assert get_badge_icons(registration) == []

    def test_returns_icons_of_registered_sessions_in_agenda_order(self, t_event) -> None:
        """Icons of registered social sessions follow the agenda (start_at) order."""
        dinner = make_social_session(t_event, "Conference dinner", "dinner")
        boat = make_social_session(t_event, "Boat trip", "boat_trip", start_at=dinner.start_at + timedelta(hours=1))
        make_social_session(t_event, "Pub quiz")  # no icon configured

        registration = RegistrationFactory(event=t_event, user=UserFactory())
        registration.sessions.add(dinner, boat)

        assert get_badge_icons(registration) == ["dinner", "boat_trip"]

    def test_dedupes_identical_icons(self, t_event) -> None:
        """Two social sessions with the same icon yield a single icon."""
        reception_one = make_social_session(t_event, "Reception one", "reception")
        reception_two = make_social_session(t_event, "Reception two", "reception")

        registration = RegistrationFactory(event=t_event, user=UserFactory())
        registration.sessions.add(reception_one, reception_two)

        assert get_badge_icons(registration) == ["reception"]

    def test_person_data_uses_selected_social_events(self, t_event) -> None:
        """With person_data, icons come from the person's selected social events."""
        dinner = make_social_session(t_event, "Conference dinner", "dinner")
        boat = make_social_session(t_event, "Boat trip", "boat_trip", start_at=dinner.start_at - timedelta(hours=2))
        reception = make_social_session(
            t_event, "Reception", "reception", start_at=dinner.start_at + timedelta(hours=1)
        )

        registration = RegistrationFactory(event=t_event, user=UserFactory())
        person = {"name": "John", "selected_social_events": [reception.id, boat.id]}

        # Icons follow agenda order (session start_at), not selection order.
        assert get_badge_icons(registration, person) == ["boat_trip", "reception"]
        assert dinner.id not in person["selected_social_events"]

    def test_ignores_unknown_icon_keys(self, t_event) -> None:
        """Icons not in the whitelist (e.g. written bypassing validation) are skipped."""
        session = make_social_session(t_event, "Mystery", "boat_trip")
        Session.objects.filter(pk=session.pk).update(extra_data={"badge_icon": "mystery"})

        registration = RegistrationFactory(event=t_event, user=UserFactory())
        registration.sessions.add(Session.objects.get(pk=session.pk))

        assert get_badge_icons(registration) == []
