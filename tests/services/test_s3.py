"""Tests for the S3 storage helpers in evan.services.s3.

The boto3 client and requests are mocked at the boundary so no network or
real S3 is touched. We assert our reaction to the library's success/failure,
not the library itself.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from evan.services import s3


@pytest.fixture
def fake_client():
    """A MagicMock standing in for the boto3 S3 client."""
    return MagicMock()


@pytest.fixture(autouse=True)
def patched_env(monkeypatch):
    """Provide deterministic S3 env vars for every test."""
    monkeypatch.setenv("S3_ENDPOINT_URL", "https://s3.example.org")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("S3_ACCESS_KEY", "key")
    monkeypatch.setenv("S3_SECRET_KEY", "secret")


@pytest.fixture
def patched_client(fake_client):
    """Patch get_s3_client to return the fake client."""
    with patch.object(s3, "get_s3_client", return_value=fake_client) as mock:
        yield mock


class TestGetS3Client:
    def test_get_s3_client_builds_client_with_env(self):
        """get_s3_client passes env-based config to boto3.client."""
        with patch("evan.services.s3.boto3.client") as mock_client:
            s3.get_s3_client()

            mock_client.assert_called_once()
            kwargs = mock_client.call_args.kwargs
            assert kwargs["service_name"] == "s3"
            assert kwargs["endpoint_url"] == "https://s3.example.org"
            assert kwargs["aws_access_key_id"] == "key"
            assert kwargs["aws_secret_access_key"] == "secret"


class TestS3StorageUrl:
    def test_url_replaces_bucket_url_with_media_prefix(self):
        """url() rewrites the bucket URL into a local /media/ path."""
        storage = s3.S3Storage()
        fake_url = "https://s3.example.org/test-bucket/path/to/file.pdf"

        with patch.object(s3.BaseS3Storage, "url", return_value=fake_url):
            result = storage.url("path/to/file.pdf")

        assert result == "/media/path/to/file.pdf"

    def test_url_returns_hash_on_exception(self):
        """url() returns a fallback '#' when the underlying call raises."""
        storage = s3.S3Storage()

        with patch.object(s3.BaseS3Storage, "url", side_effect=Exception("boom")):
            result = storage.url("missing.pdf")

        assert result == "#"


class TestBucketOperations:
    def test_create_bucket_calls_client(self, patched_client, fake_client):
        """create_bucket delegates to the S3 client with the bucket name."""
        s3.create_bucket("my-bucket")

        fake_client.create_bucket.assert_called_once_with(Bucket="my-bucket")

    def test_list_bucket_files_returns_keys(self, patched_client, fake_client):
        """list_bucket_files extracts the Key of each listed object."""
        fake_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "a.txt"},
                {"Key": "b.txt"},
            ]
        }

        result = s3.list_bucket_files("my-bucket")

        assert result == ["a.txt", "b.txt"]

    def test_list_bucket_files_empty_when_no_contents(self, patched_client, fake_client):
        """list_bucket_files returns an empty list when Contents is missing."""
        fake_client.list_objects_v2.return_value = {}

        result = s3.list_bucket_files("my-bucket")

        assert result == []

    def test_empty_bucket_deletes_each_object(self, patched_client, fake_client):
        """empty_bucket deletes every object returned by the listing."""
        fake_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "a.txt"},
                {"Key": "b.txt"},
            ]
        }

        s3.empty_bucket("my-bucket")

        assert fake_client.delete_object.call_count == 2
        fake_client.delete_object.assert_any_call(Bucket="my-bucket", Key="a.txt")
        fake_client.delete_object.assert_any_call(Bucket="my-bucket", Key="b.txt")

    def test_empty_bucket_noop_when_empty(self, patched_client, fake_client):
        """empty_bucket does not delete anything when there are no objects."""
        fake_client.list_objects_v2.return_value = {}

        s3.empty_bucket("my-bucket")

        fake_client.delete_object.assert_not_called()


class TestDeleteS3Object:
    def test_delete_skips_when_not_production(self, patched_client, fake_client, settings):
        """delete_s3_object is a no-op outside production."""
        settings.ENV = "development"

        s3.delete_s3_object("some/key")

        fake_client.delete_object.assert_not_called()

    def test_delete_in_production_calls_client(self, patched_client, fake_client, settings):
        """delete_s3_object deletes the object in production."""
        settings.ENV = "production"

        s3.delete_s3_object("some/key")

        fake_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="some/key",
        )


class TestPresignedUrl:
    def test_get_s3_presigned_url_passes_params(self, patched_client, fake_client):
        """get_s3_presigned_url forwards bucket, key, and expiry to the client."""
        fake_client.generate_presigned_url.return_value = "https://presigned"

        result = s3.get_s3_presigned_url("the/key", expires_in=120)

        fake_client.generate_presigned_url.assert_called_once_with(
            ClientMethod="get_object",
            ExpiresIn=120,
            Params={"Bucket": "test-bucket", "Key": "the/key"},
        )
        assert result == "https://presigned"


class TestGetS3Response:
    def test_get_s3_response_returns_response_on_success(self, patched_client, fake_client):
        """get_s3_response returns the streaming response when status is OK."""
        fake_response = MagicMock(spec=requests.Response)
        with patch("evan.services.s3.requests.get", return_value=fake_response) as mock_get:
            result = s3.get_s3_response("the/key")

        assert result is fake_response
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["stream"] is True
        assert call_kwargs["timeout"] == 10

    def test_get_s3_response_raises_on_http_error(self, patched_client, fake_client):
        """get_s3_response re-raises when the response indicates an error."""
        fake_response = MagicMock(spec=requests.Response)
        fake_response.raise_for_status.side_effect = requests.HTTPError("bad")

        with patch("evan.services.s3.requests.get", return_value=fake_response), pytest.raises(requests.HTTPError):
            s3.get_s3_response("the/key")
