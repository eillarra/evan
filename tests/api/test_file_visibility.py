"""Tests that files embedded in API responses honour private/public visibility.

Private files must only appear to users who can actually access them
(accepted attendees and event managers); anonymous users only ever see
public files.
"""

import pytest
from django.core.files.base import ContentFile

from evan.models import File
from evan.models.rel.permissions import Permission
from tests._factories import RegistrationFactory, UserFactory


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def event_files(t_event):
    """Attach one public and one private file to the event."""
    public = File.objects.create(
        content_object=t_event,
        type=File.PUBLIC,
        file=ContentFile(b"public", name="event/logo.png"),
    )
    private = File.objects.create(
        content_object=t_event,
        type=File.PRIVATE,
        file=ContentFile(b"private", name="event/proceedings.pdf"),
    )
    return public, private


def _file_names(response) -> list[str]:
    return [entry["file"] for entry in response.json()["files"]]


@pytest.mark.api
@pytest.mark.django_db
class TestEventFilesVisibility:
    """Files in the event detail response honour private/public visibility."""

    def test_anonymous_user_sees_only_public_files(self, api_client, t_event, event_files):
        """Anonymous responses must not include private file metadata."""
        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert len(names) == 1
        assert "proceedings" not in names[0]

    def test_accepted_attendee_sees_private_files(self, api_client, t_event, event_files):
        """An accepted attendee sees the private file in the response."""
        user = UserFactory()
        RegistrationFactory(event=t_event, user=user, is_accepted=True)
        api_client.force_authenticate(user=user)

        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert any("proceedings" in name for name in names)

    def test_unregistered_user_sees_only_public_files(self, api_client, t_event, event_files):
        """An authenticated user without a registration must not see the private file."""
        api_client.force_authenticate(user=UserFactory())

        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert len(names) == 1
        assert "proceedings" not in names[0]

    def test_event_manager_sees_private_files(self, api_client, t_event, event_files):
        """Event managers see the private file in the response."""
        user = UserFactory()
        Permission.objects.create(content_object=t_event, user=user, level=Permission.ADMIN)
        api_client.force_authenticate(user=user)

        response = api_client.get(t_event.get_api_url())

        names = _file_names(response)
        assert any("proceedings" in name for name in names)
