"""Tests for the temporary file relocation command.

The command moves files stored under the old visibility-prefixed key to the
visibility-free layout. It must be safe to run twice and must leave the old
objects in place.
"""

import io
from unittest.mock import patch

import pytest

from evan.models import File
from tests._factories import SessionFactory


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


def _legacy_file(session, key="private/47/1/slides.pdf") -> File:
    """Create a file stored under a legacy visibility-prefixed key.

    The model computes the storage key on every save, so the legacy key is
    written straight to the row, the way the old uploads left it.
    """
    file = File.objects.create(content_object=session, visibility=File.ATTENDEES, file="slides.pdf")
    File.objects.filter(pk=file.pk).update(file=key)
    file.refresh_from_db()
    return file


@pytest.mark.django_db
class TestRelocateFilesCommand:
    """The command rewrites the rows and copies the objects."""

    def test_no_legacy_files_reports_nothing(self, db):
        """A run without legacy files says so and changes nothing."""
        from django.core.management import call_command

        out = io.StringIO()
        call_command("relocate_files", stdout=out)

        assert "No files to relocate" in out.getvalue()

    def test_legacy_file_is_relocated(self, db):
        """A legacy file is copied to the visibility-free key and its row rewritten."""
        from django.core.management import call_command

        session = SessionFactory()
        file = _legacy_file(session)

        with (
            patch("evan.management.commands.relocate_files.copy_s3_object") as mock_copy,
            patch("evan.management.commands.relocate_files.get_s3_client"),
        ):
            call_command("relocate_files", stdout=io.StringIO())

        file.refresh_from_db()
        assert file.file.name == "files/47/1/slides.pdf"
        mock_copy.assert_called_once_with("private/47/1/slides.pdf", "files/47/1/slides.pdf")

    def test_dry_run_changes_nothing(self, db):
        """A dry run reports the move without touching the storage or the rows."""
        from django.core.management import call_command

        session = SessionFactory()
        file = _legacy_file(session)

        with (
            patch("evan.management.commands.relocate_files.copy_s3_object") as mock_copy,
            patch("evan.management.commands.relocate_files.get_s3_client"),
        ):
            call_command("relocate_files", "--dry-run", stdout=io.StringIO())

        file.refresh_from_db()
        assert file.file.name == "private/47/1/slides.pdf"
        mock_copy.assert_not_called()

    def test_running_twice_is_safe(self, db):
        """A second run finds nothing left to relocate."""
        from django.core.management import call_command

        session = SessionFactory()
        _legacy_file(session)

        with (
            patch("evan.management.commands.relocate_files.copy_s3_object") as mock_copy,
            patch("evan.management.commands.relocate_files.get_s3_client"),
        ):
            call_command("relocate_files", stdout=io.StringIO())
            call_command("relocate_files", stdout=io.StringIO())

        assert mock_copy.call_count == 1

    def test_the_old_object_is_not_deleted_by_default(self, db):
        """The old object is left in place: the old layout keeps working."""
        from django.core.management import call_command

        session = SessionFactory()
        _legacy_file(session)

        with (
            patch("evan.management.commands.relocate_files.copy_s3_object"),
            patch("evan.management.commands.relocate_files.get_s3_client") as mock_client,
        ):
            call_command("relocate_files", stdout=io.StringIO())

        mock_client.return_value.delete_object.assert_not_called()
