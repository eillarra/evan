"""Tests for the file visibility tiers and the storage layout they use.

The tier decides who may see a file; the stored key never mentions the tier,
so an audience change never moves the stored object.
"""

import pytest
from django.core.files.base import ContentFile

from evan.models import Fee, File
from evan.models.rel.permissions import Permission
from tests._factories import EventFactory, RegistrationFactory, SessionFactory, UserFactory


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


def _add_fee(event) -> None:
    """Give the event a regular fee, so registrations can be created."""
    Fee.objects.create(event=event, type="regular", value=100)


@pytest.fixture
def session(db):
    """A session attached to its own event."""
    return SessionFactory()


@pytest.mark.django_db
class TestUploadPath:
    """The stored key names the owning object, never the visibility tier."""

    def test_stored_key_has_no_visibility_segment(self, session):
        """A new file's key carries no visibility tier."""
        file = File.objects.create(
            content_object=session,
            visibility=File.ORGANIZERS,
            file=ContentFile(b"slides", name="slides.pdf"),
        )

        assert not file.file.name.startswith(("public/", "private/", "attendees/", "organizers/"))
        assert file.file.name.startswith(f"files/{file.content_type_id}/{session.pk}/")

    def test_two_uploads_with_the_same_name_get_distinct_keys(self, session):
        """Two files with the same original name never overwrite each other."""
        first = File.objects.create(
            content_object=session,
            visibility=File.ATTENDEES,
            file=ContentFile(b"one", name="slides.pdf"),
        )
        second = File.objects.create(
            content_object=session,
            visibility=File.ATTENDEES,
            file=ContentFile(b"two", name="slides.pdf"),
        )

        assert first.file.name != second.file.name

    def test_changing_the_visibility_keeps_the_stored_object(self, session):
        """A tier change is a row update: the stored object does not move."""
        file = File.objects.create(
            content_object=session,
            visibility=File.PUBLIC,
            file=ContentFile(b"slides", name="slides.pdf"),
        )
        original_name = file.file.name

        file.visibility = File.ORGANIZERS
        file.save()

        file.refresh_from_db()
        assert file.visibility == File.ORGANIZERS
        assert file.file.name == original_name


@pytest.mark.django_db
class TestVisibilityTiers:
    """The tier constants and the ``is_public`` shortcut."""

    def test_default_visibility_is_attendees(self, session):
        """A file without an explicit tier is attendee-tier."""
        file = File.objects.create(content_object=session, file=ContentFile(b"slides", name="slides.pdf"))

        assert file.visibility == File.ATTENDEES

    def test_is_public_only_for_the_public_tier(self, session):
        """``is_public`` is true only for the public tier."""
        public = File.objects.create(
            content_object=session,
            visibility=File.PUBLIC,
            file=ContentFile(b"a", name="a.pdf"),
        )
        attendees = File.objects.create(
            content_object=session,
            visibility=File.ATTENDEES,
            file=ContentFile(b"b", name="b.pdf"),
        )

        assert public.is_public is True
        assert attendees.is_public is False


@pytest.mark.django_db
class TestSessionFileManagement:
    """A session's organizers are the event's managers and the session's own admins."""

    def test_event_manager_can_manage_session_files(self, db):
        """An event manager may manage a session's files."""
        session = SessionFactory()
        user = UserFactory()
        Permission.objects.create(content_object=session.event, user=user, level=Permission.ADMIN)

        assert session.files_can_be_managed_by(user) is True

    def test_session_admin_can_manage_session_files(self, db):
        """A session's own administrator may manage the session's files."""
        session = SessionFactory()
        user = UserFactory()
        Permission.objects.create(content_object=session, user=user, level=Permission.ADMIN)

        assert session.files_can_be_managed_by(user) is True

    def test_ordinary_attendee_cannot_manage_session_files(self, db):
        """An accepted attendee may not manage a session's files."""
        session = SessionFactory()
        _add_fee(session.event)
        user = UserFactory()
        RegistrationFactory(event=session.event, user=user, is_accepted=True)

        assert session.files_can_be_managed_by(user) is False

    def test_unregistered_user_cannot_manage_session_files(self, db):
        """An authenticated user without registration may not manage a session's files."""
        session = SessionFactory()

        assert session.files_can_be_managed_by(UserFactory()) is False


@pytest.mark.django_db
class TestAbstractFileAccess:
    """An abstract's attendee-tier files follow the accepted-registration rule."""

    def test_pending_registrant_is_denied(self, db):
        """A pending registrant cannot reach an accepted abstract's files."""
        from evan.models import Abstract

        event = EventFactory(accept_by_default=False)
        _add_fee(event)
        abstract = Abstract.objects.create(
            event=event,
            user=UserFactory(),
            title="Test abstract",
            authors="Test author",
            abstract="Test body",
            is_accepted=True,
        )
        user = UserFactory()
        RegistrationFactory(event=event, user=user, is_accepted=None)

        assert abstract.files_viewable_by_user(user) is False

    def test_accepted_registrant_is_allowed(self, db):
        """An accepted registrant may reach an accepted abstract's files."""
        from evan.models import Abstract

        event = EventFactory()
        _add_fee(event)
        abstract = Abstract.objects.create(
            event=event,
            user=UserFactory(),
            title="Test abstract",
            authors="Test author",
            abstract="Test body",
            is_accepted=True,
        )
        user = UserFactory()
        RegistrationFactory(event=event, user=user, is_accepted=True)

        assert abstract.files_viewable_by_user(user) is True
