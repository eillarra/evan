from http import HTTPStatus as status

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from evan.utils.factories import ContentFactory, UserFactory


@pytest.fixture
def content(db, test_event):
    return ContentFactory(
        event=test_event,
        config={
            "file_uploader": {
                "max_files": 1,
            },
        },
    )


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
class TestForAnonymous:
    expected_status_codes: dict[str, status] = {
        "upload": status.FORBIDDEN,
    }

    def test_file_upload(self, api_client, content) -> None:
        url = content.get_api_url() + "files/"
        response = api_client.post(
            url,
            {"file": SimpleUploadedFile("test.txt", b"file content")},
            headers={"Content-Disposition": "attachment; filename=test.txt"},
        )
        assert response.status_code == self.expected_status_codes["upload"]


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestForEventManager(TestForAuthenticated):
    expected_status_codes = {
        "upload": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, test_event_manager):
        api_client.force_authenticate(user=test_event_manager)

    def test_second_file_upload_should_fail(self, api_client, content) -> None:
        url = content.get_api_url() + "files/"

        for file, response_code in [("test1.txt", status.OK), ("test2.txt", status.BAD_REQUEST)]:
            response = api_client.post(
                url,
                {"file": SimpleUploadedFile(file, b"file content")},
                headers={"Content-Disposition": f"attachment; filename={file}"},
            )
            assert response.status_code == response_code
