"""Tests that files embedded in API responses honour their visibility tier.

A file's tier decides who may see it: public files are open to everyone,
attendees-tier files to accepted attendees and organizers, organizers-tier files
to the object's organizers only. Anonymous responses only ever show public
files.
"""

import pytest
from django.core.files.base import ContentFile

from evan.models import File
from evan.models.rel.permissions import Permission
from tests._factories import PaperFactory, RegistrationFactory, SessionFactory, UserFactory


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def event_files(t_event):
    """Attach one file per visibility tier to the event."""
    public = File.objects.create(
        content_object=t_event,
        visibility=File.PUBLIC,
        file=ContentFile(b"public", name="event/logo.png"),
    )
    attendees = File.objects.create(
        content_object=t_event,
        visibility=File.ATTENDEES,
        file=ContentFile(b"attendees", name="event/proceedings.pdf"),
    )
    organizers = File.objects.create(
        content_object=t_event,
        visibility=File.ORGANIZERS,
        file=ContentFile(b"organizers", name="event/budget.xlsx"),
    )
    return public, attendees, organizers


def _file_names(response) -> list[str]:
    return [entry["file"] for entry in response.json()["files"]]


def _visibilities(response) -> list[str]:
    return [entry["visibility"] for entry in response.json()["files"]]


@pytest.mark.api
@pytest.mark.django_db
class TestEventFilesVisibility:
    """Files in the event detail response honour their visibility tier."""

    def test_anonymous_user_sees_only_public_files(self, api_client, t_event, event_files):
        """Anonymous responses must not include non-public file metadata."""
        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert len(names) == 1
        assert "proceedings" not in names[0]
        assert "budget" not in names[0]

    def test_accepted_attendee_sees_attendees_files_only(self, api_client, t_event, event_files):
        """An accepted attendee sees the attendees-tier file, not the organizers-tier one."""
        user = UserFactory()
        RegistrationFactory(event=t_event, user=user, is_accepted=True)
        api_client.force_authenticate(user=user)

        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert any("proceedings" in name for name in names)
        assert not any("budget" in name for name in names)

    def test_unregistered_user_sees_only_public_files(self, api_client, t_event, event_files):
        """An authenticated user without a registration must not see the non-public files."""
        api_client.force_authenticate(user=UserFactory())

        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert len(names) == 1
        assert "proceedings" not in names[0]
        assert "budget" not in names[0]

    def test_event_manager_sees_all_files(self, api_client, t_event, event_files):
        """Event managers see every tier."""
        user = UserFactory()
        Permission.objects.create(content_object=t_event, user=user, level=Permission.ADMIN)
        api_client.force_authenticate(user=user)

        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert any("proceedings" in name for name in names)
        assert any("budget" in name for name in names)

    def test_visibility_is_exposed_in_the_response(self, api_client, t_event, event_files):
        """The response exposes the tier, not the old binary flag."""
        user = UserFactory()
        Permission.objects.create(content_object=t_event, user=user, level=Permission.ADMIN)
        api_client.force_authenticate(user=user)

        response = api_client.get(t_event.get_api_url())

        assert set(_visibilities(response)) == {File.PUBLIC, File.ATTENDEES, File.ORGANIZERS}
        assert "type" not in response.json()["files"][0]


@pytest.mark.api
@pytest.mark.django_db
class TestSecretScopedFileLists:
    """A secret reveals the files only of the object that accepts it."""

    @staticmethod
    def _material(content_object, name="session/budget.pdf"):
        return File.objects.create(
            content_object=content_object,
            visibility=File.ORGANIZERS,
            file=ContentFile(b"material", name=name),
        )

    def test_session_secret_reveals_its_organizers_material(self, api_client, t_event):
        """The session's secret link holder sees the organizers-tier material."""
        session = SessionFactory(event=t_event)
        self._material(session)

        response = api_client.get(session.get_api_url(), headers={"X-Evan-Secret": session.secret})

        assert _visibilities(response) == [File.ORGANIZERS]

    def test_without_the_secret_the_material_stays_hidden(self, api_client, t_event):
        """The same response shows nothing to a visitor without the secret."""
        session = SessionFactory(event=t_event)
        self._material(session)

        response = api_client.get(session.get_api_url())

        assert _visibilities(response) == []

    def test_paper_secret_reveals_nothing(self, api_client, db):
        """A paper's editing link is not a credential for the paper's files."""
        paper = PaperFactory()
        self._material(paper, name="paper/draft.pdf")

        response = api_client.get(paper.get_api_url(), headers={"X-Evan-Secret": paper.secret})

        assert _visibilities(response) == []
