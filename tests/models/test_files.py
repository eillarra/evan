"""Tests for storage cleanup when files (or their owners) are deleted.

The S3 client is mocked at the boundary so no real bucket is ever touched.
Storage cleanup is scheduled with ``transaction.on_commit`` from a
``post_delete`` signal, so the tests use ``capture_on_commit_callbacks`` to
surface those callbacks on the test database connection.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from django.core.files.base import ContentFile
from django.db import transaction

from evan.models import File
from evan.services import s3


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def production_s3(settings, monkeypatch):
    """Make storage deletes run against a mocked S3 client."""
    client = MagicMock()
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    settings.ENV = "production"
    with patch.object(s3, "get_s3_client", return_value=client):
        yield client


def attach_file(content_object, name="event/proceedings.pdf") -> File:
    """Attach a file to the given content object."""
    return File.objects.create(
        content_object=content_object,
        type=File.PRIVATE,
        file=ContentFile(b"file content", name=name),
    )


@pytest.mark.django_db
class TestFileStorageCleanup:
    """Deleting a file, or its owner, removes the object from storage."""

    def test_deleting_owner_deletes_object_from_storage(
        self, t_event, production_s3, django_capture_on_commit_callbacks
    ):
        """Deleting the owner schedules and runs the S3 delete."""
        file = attach_file(t_event)

        with django_capture_on_commit_callbacks(execute=True):
            t_event.delete()

        production_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key=file.file.name)
        assert not File.objects.filter(pk=file.pk).exists()

    def test_deleting_file_deletes_object_from_storage(
        self, t_event, production_s3, django_capture_on_commit_callbacks
    ):
        """Deleting the file itself schedules and runs the S3 delete."""
        file = attach_file(t_event)

        with django_capture_on_commit_callbacks(execute=True):
            file.delete()

        production_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key=file.file.name)

    def test_storage_failure_is_logged_but_delete_succeeds(
        self, t_event, production_s3, caplog, django_capture_on_commit_callbacks
    ):
        """A failing S3 delete is logged; the DB delete still succeeds."""
        file = attach_file(t_event)
        production_s3.delete_object.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "boom"}}, "DeleteObject"
        )

        caplog.set_level(logging.ERROR, logger="evan.models.rel.files")
        with django_capture_on_commit_callbacks(execute=True):
            t_event.delete()

        assert not File.objects.filter(pk=file.pk).exists()
        production_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key=file.file.name)
        assert "Failed to delete" in caplog.text

    def test_transaction_rollback_never_deletes_from_storage(
        self, t_event, production_s3, django_capture_on_commit_callbacks
    ):
        """A rolled-back transaction never schedules the S3 delete."""
        attach_file(t_event)

        with pytest.raises(ValueError), transaction.atomic(), django_capture_on_commit_callbacks():
            t_event.delete()
            raise ValueError

        production_s3.delete_object.assert_not_called()
