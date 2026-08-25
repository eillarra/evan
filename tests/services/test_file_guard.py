"""Tests for evan.services.file_guard.check_file_access.

Access control for private files lives in one place. These tests cover the
album branch (attendee/no-show/manager) and the generic
files_can_be_managed_by fallback branch.
"""

import pytest
from django.contrib.auth.models import AnonymousUser

from evan.models import File
from evan.services.file_guard import check_file_access
from tests._factories import AlbumFactory, EventFactory, RegistrationFactory, UserFactory


@pytest.fixture
def event(db):
    """A standalone event for generic-file tests."""
    return EventFactory()


@pytest.fixture
def album(t_event):
    """An album attached to the shared t_event fixture."""
    return AlbumFactory(event=t_event)


def _make_file(content_object, file_type=File.PRIVATE, path="album/photo.jpg"):
    """Create a File attached to the given content object."""
    return File.objects.create(content_object=content_object, type=file_type, file=path)


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
class TestCheckFileAccessGeneric:
    """check_file_access behaviour for non-album files (fallback branch)."""

    def test_manager_can_access_event_file(self, event):
        """Event managers fall through to files_can_be_managed_by."""
        from evan.models import Permission

        file = _make_file(event, path="event/program.pdf")
        user = UserFactory()
        Permission.objects.create(content_object=event, user=user, level=Permission.ADMIN)

        assert check_file_access(file, user) is True

    def test_non_manager_is_denied_event_file(self, event):
        """Users without manager permission fall through and are denied."""
        file = _make_file(event, path="event/program.pdf")
        user = UserFactory()

        assert check_file_access(file, user) is False

    def test_anonymous_user_denied_for_event_file(self, event):
        """Anonymous users are denied before the fallback branch runs."""
        file = _make_file(event, path="event/program.pdf")

        assert check_file_access(file, AnonymousUser()) is False
