from http import HTTPStatus as status

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from evan.utils.factories import ContentFactory, UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def content_max_files_1(db, t_event):
    return ContentFactory(event=t_event, config={"file_uploader": {"max_files": 1}})


@pytest.fixture
def content_max_files_key_missing_defaults_to_1(db, t_event):
    return ContentFactory(event=t_event, config={"file_uploader": {}})


@pytest.mark.api
class TestForAnonymous:
    expected_status_codes: dict[str, status] = {
        "upload": status.FORBIDDEN,
    }

    def test_file_upload(self, api_client, content_max_files_1) -> None:
        content_obj = content_max_files_1
        content_type_id = ContentType.objects.get_for_model(content_obj).id
        url = reverse(
            "v1:file-list",
            kwargs={
                "parent_lookup_content_type_id": content_type_id,
                "parent_lookup_object_id": content_obj.pk,
            },
        )
        response = api_client.post(
            url,
            {"file": SimpleUploadedFile("test.txt", b"file content")},
            headers={"Content-Disposition": "attachment; filename=test.txt"},
            format="multipart",
        )
        assert response.status_code == self.expected_status_codes["upload"]


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup_authenticated(self, api_client, user):
        api_client.force_authenticate(user=user)

    def test_file_upload(self, api_client, content_max_files_1) -> None:
        super().test_file_upload(api_client, content_max_files_1)


class TestForEventManager(TestForAuthenticated):
    expected_status_codes: dict[str, status] = {
        "upload": status.CREATED,
    }

    @pytest.fixture(autouse=True)
    def setup_event_manager(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def _upload_file(self, api_client, content_obj, filename="test.txt"):
        content_type_id = ContentType.objects.get_for_model(content_obj).id
        url = reverse(
            "v1:file-list",
            kwargs={
                "parent_lookup_content_type_id": content_type_id,
                "parent_lookup_object_id": content_obj.pk,
            },
        )
        return api_client.post(
            url,
            {"file": SimpleUploadedFile(filename, b"file content")},
            headers={"Content-Disposition": f"attachment; filename={filename}"},
            format="multipart",
        )

    def test_upload_with_max_files_1(self, api_client, content_max_files_1):
        response1 = self._upload_file(api_client, content_max_files_1, "file1.txt")
        assert response1.status_code == status.CREATED, response1.data

        response2 = self._upload_file(api_client, content_max_files_1, "file2.txt")
        assert response2.status_code == status.BAD_REQUEST, response2.data

    def test_upload_with_max_files_key_missing_defaults_to_1(
        self, api_client, content_max_files_key_missing_defaults_to_1
    ):
        response1 = self._upload_file(api_client, content_max_files_key_missing_defaults_to_1, "file1.txt")
        assert response1.status_code == status.CREATED, response1.data

        response2 = self._upload_file(api_client, content_max_files_key_missing_defaults_to_1, "file2.txt")
        assert response2.status_code == status.BAD_REQUEST, response2.data
