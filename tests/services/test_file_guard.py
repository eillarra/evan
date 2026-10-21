"""Tests for evan.services.file_guard.check_file_access.

Access control for non-public files lives in one place. These tests cover the
visibility tiers (public, attendees, organizers), the model-level
``files_viewable_by_user`` / ``files_can_be_managed_by`` implementations: the
FilesMixin default (managers or accepted attendees), the Album override (no
no-shows) and Event-specific behaviour, plus the secret that unlocks an
object's own files.
"""

import pytest
from django.contrib.auth.models import AnonymousUser

from evan.models import File
from evan.services.file_guard import check_file_access
from tests._factories import (
    AlbumFactory,
    ContentFactory,
    EventFactory,
    RegistrationFactory,
    SessionFactory,
    UserFactory,
)


@pytest.fixture
def event(db):
    """A standalone event (with a regular fee) for event-file tests."""
    from evan.models import Fee

    event = EventFactory()
    Fee.objects.create(event=event, type="regular", value=100)
    return event


@pytest.fixture
def content(event):
    """A content object attached to the standalone event for fallback tests."""
    return ContentFactory(event=event)


@pytest.fixture
def album(t_event):
    """An album attached to the shared t_event fixture."""
    return AlbumFactory(event=t_event)


def _make_file(content_object, visibility=File.ATTENDEES, path="album/photo.jpg"):
    """Create a File attached to the given content object."""
    return File.objects.create(content_object=content_object, visibility=visibility, file=path)


@pytest.mark.django_db
class TestCheckFileAccessAlbum:
    """check_file_access behaviour when the file's content object is an Album."""

    def test_anonymous_user_is_denied(self, album):
        """Unauthenticated users never get access to private files."""
        file = _make_file(album)
        user = AnonymousUser()

        assert check_file_access(file, user) is False

    def test_attending_user_is_allowed(self, album, t_event):
        """A registered, accepted, non-no-show attendee can access album files."""
        file = _make_file(album)
        user = UserFactory()
        RegistrationFactory(event=t_event, user=user, is_accepted=True, no_show=False)

        assert check_file_access(file, user) is True

    def test_no_show_user_is_denied(self, album, t_event):
        """A no-show attendee cannot access album files."""
        file = _make_file(album)
        user = UserFactory()
        RegistrationFactory(event=t_event, user=user, is_accepted=True, no_show=True)

        assert check_file_access(file, user) is False

    def test_not_registered_user_is_denied(self, album):
        """An authenticated user with no registration cannot access album files."""
        file = _make_file(album)
        user = UserFactory()

        assert check_file_access(file, user) is False

    def test_event_manager_is_allowed(self, album, t_event_manager):
        """Event managers can access album files."""
        file = _make_file(album)

        assert check_file_access(file, t_event_manager) is True


@pytest.mark.django_db
class TestCheckFileAccessEvent:
    """check_file_access behaviour when the file's content object is an Event."""

    def test_anonymous_user_is_denied(self, event):
        """Unauthenticated users never get access to private files."""
        file = _make_file(event, path="event/proceedings.pdf")

        assert check_file_access(file, AnonymousUser()) is False

    def test_accepted_attendee_is_allowed(self, event):
        """A registered, accepted attendee can access private event files."""
        file = _make_file(event, path="event/proceedings.pdf")
        user = UserFactory()
        RegistrationFactory(event=event, user=user, is_accepted=True)

        assert check_file_access(file, user) is True

    def test_pending_attendee_is_denied(self, db):
        """A registered user whose registration is still pending cannot access private event files."""
        from evan.models import Fee

        event = EventFactory(accept_by_default=False)
        Fee.objects.create(event=event, type="regular", value=100)
        file = _make_file(event, path="event/proceedings.pdf")
        user = UserFactory()
        RegistrationFactory(event=event, user=user, is_accepted=None)

        assert check_file_access(file, user) is False

    def test_declined_attendee_is_denied(self, event):
        """A registered user whose registration was declined cannot access private event files."""
        file = _make_file(event, path="event/proceedings.pdf")
        user = UserFactory()
        registration = RegistrationFactory(event=event, user=user)
        registration.is_accepted = False
        registration.save()

        assert check_file_access(file, user) is False

    def test_not_registered_user_is_denied(self, event):
        """An authenticated user with no registration cannot access private event files."""
        file = _make_file(event, path="event/proceedings.pdf")
        user = UserFactory()

        assert check_file_access(file, user) is False

    def test_event_manager_is_allowed(self, event):
        """Event managers can access private event files."""
        from evan.models import Permission

        file = _make_file(event, path="event/proceedings.pdf")
        user = UserFactory()
        Permission.objects.create(content_object=event, user=user, level=Permission.ADMIN)

        assert check_file_access(file, user) is True


@pytest.mark.django_db
class TestCheckFileAccessFallback:
    """check_file_access for FilesMixin models without their own override (default rule)."""

    def test_manager_can_access_content_file(self, content):
        """Event managers fall through to files_can_be_managed_by."""
        from evan.models import Permission

        file = _make_file(content, path="content/banner.pdf")
        user = UserFactory()
        Permission.objects.create(content_object=content.event, user=user, level=Permission.ADMIN)

        assert check_file_access(file, user) is True

    def test_non_manager_is_denied_content_file(self, content):
        """Users without manager permission fall through and are denied."""
        file = _make_file(content, path="content/banner.pdf")
        user = UserFactory()

        assert check_file_access(file, user) is False

    def test_anonymous_user_denied_for_content_file(self, content):
        """Anonymous users are denied before the fallback branch runs."""
        file = _make_file(content, path="content/banner.pdf")

        assert check_file_access(file, AnonymousUser()) is False


@pytest.mark.django_db
class TestCheckFileAccessVisibilityTiers:
    """Each visibility tier resolves to its own audience."""

    def test_public_file_is_allowed_to_anonymous_user(self, event):
        """A public file is served to anyone, including anonymous visitors."""
        file = _make_file(event, visibility=File.PUBLIC, path="event/logo.png")

        assert check_file_access(file, AnonymousUser()) is True

    def test_attendees_file_is_allowed_to_accepted_attendee(self, event):
        """An accepted attendee may access an attendees-tier file."""
        file = _make_file(event, visibility=File.ATTENDEES, path="event/proceedings.pdf")
        user = UserFactory()
        RegistrationFactory(event=event, user=user, is_accepted=True)

        assert check_file_access(file, user) is True

    def test_attendees_file_is_denied_to_pending_attendee(self, db):
        """A pending registrant may not access an attendees-tier file."""
        from evan.models import Fee

        event = EventFactory(accept_by_default=False)
        Fee.objects.create(event=event, type="regular", value=100)
        file = _make_file(event, visibility=File.ATTENDEES, path="event/proceedings.pdf")
        user = UserFactory()
        RegistrationFactory(event=event, user=user, is_accepted=None)

        assert check_file_access(file, user) is False

    def test_attendees_file_is_denied_to_unregistered_user(self, event):
        """An authenticated user without registration may not access an attendees-tier file."""
        file = _make_file(event, visibility=File.ATTENDEES, path="event/proceedings.pdf")

        assert check_file_access(file, UserFactory()) is False

    def test_organizers_file_is_denied_to_accepted_attendee(self, event):
        """An accepted attendee may not access an organizers-tier file."""
        file = _make_file(event, visibility=File.ORGANIZERS, path="event/budget.xlsx")
        user = UserFactory()
        RegistrationFactory(event=event, user=user, is_accepted=True)

        assert check_file_access(file, user) is False

    def test_organizers_file_is_allowed_to_event_manager(self, event):
        """An event manager may access an organizers-tier file."""
        from evan.models import Permission

        file = _make_file(event, visibility=File.ORGANIZERS, path="event/budget.xlsx")
        user = UserFactory()
        Permission.objects.create(content_object=event, user=user, level=Permission.ADMIN)

        assert check_file_access(file, user) is True


@pytest.mark.django_db
class TestCheckFileAccessSecret:
    """The owning object's secret unlocks that object's own files."""

    def test_secret_unlocks_the_owning_object_file(self, db):
        """A session's secret opens an organizers-tier file of that session."""
        session = SessionFactory()
        file = _make_file(session, visibility=File.ORGANIZERS, path="session/slides.pdf")

        assert check_file_access(file, AnonymousUser(), secret=session.secret) is True

    def test_foreign_secret_is_refused(self, db):
        """Another session's secret does not open this session's file."""
        session = SessionFactory()
        other_session = SessionFactory()
        file = _make_file(session, visibility=File.ORGANIZERS, path="session/slides.pdf")

        assert check_file_access(file, AnonymousUser(), secret=other_session.secret) is False

    def test_secret_does_not_unlock_another_objects_file(self, db):
        """A session's secret grants nothing on another session's file."""
        session = SessionFactory()
        other_session = SessionFactory()
        file = _make_file(other_session, visibility=File.ORGANIZERS, path="session/slides.pdf")

        assert check_file_access(file, AnonymousUser(), secret=session.secret) is False

    def test_wrong_secret_is_refused(self, db):
        """A wrong secret does not open the file."""
        session = SessionFactory()
        file = _make_file(session, visibility=File.ORGANIZERS, path="session/slides.pdf")

        assert check_file_access(file, AnonymousUser(), secret="not-the-secret") is False
