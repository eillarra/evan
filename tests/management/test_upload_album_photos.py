"""Tests for the upload_album_photos management command.

A dry run must be read-only: it lists the photos it would upload and writes
nothing, not even the album row.
"""

import io
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from evan.models import Album, File
from tests._factories import EventFactory


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so the run test never touches real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


def run_command(event, album_title: str, photos_path, *args: str, stdout=None):
    """Invoke the command with one photo in the folder."""
    (photos_path / "photo.jpg").write_bytes(b"dummy jpeg content")
    out = stdout or io.StringIO()

    call_command("upload_album_photos", event.code, album_title, str(photos_path), *args, stdout=out)

    return out


@pytest.mark.django_db
class TestUploadAlbumPhotosDryRun:
    """--dry-run reports the photos without writing anything."""

    def test_dry_run_does_not_create_the_album(self, tmp_path):
        """A dry run on a new title leaves no album and no file behind."""
        event = EventFactory()
        album_title = "New album"

        out = run_command(event, album_title, tmp_path, "--dry-run")

        assert not Album.objects.filter(event=event, title=album_title).exists()
        assert not File.objects.exists()
        assert "Would upload: photo.jpg" in out.getvalue()

    def test_run_creates_the_album_and_uploads_the_photo(self, tmp_path):
        """The same setup without --dry-run does create the album, so the dry run is what keeps it out."""
        event = EventFactory()
        album_title = "New album"
        original = SimpleUploadedFile("photo.jpg", b"dummy jpeg content", content_type="image/jpeg")

        with patch(
            "evan.management.commands.upload_album_photos.ImageProcessor.process_image",
            return_value=original,
        ):
            out = run_command(event, album_title, tmp_path)

        assert Album.objects.filter(event=event, title=album_title).exists()
        assert File.objects.filter(object_id=Album.objects.get(title=album_title).pk).count() == 2
        assert "Successfully uploaded 1 photos" in out.getvalue()
