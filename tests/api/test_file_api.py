"""Tests for the file API: visibility tiers, uploader configuration and secrets.

The uploader configuration is declared on the owning object (or the viewset) and
now enforced: how many files, which types, which visibility tiers, and which
tier a new file gets by default. A session's secret manages that session's
files, and nothing else.
"""

import json
from http import HTTPStatus as status

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from evan.models import File
from tests._factories import ContentFactory, PaperFactory, SessionFactory


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


def _file_url(obj) -> str:
    """Return the nested file collection URL of an object."""
    content_type_id = ContentType.objects.get_for_model(obj).id
    return reverse(
        "v1:file-list",
        kwargs={
            "parent_lookup_content_type_id": content_type_id,
            "parent_lookup_object_id": obj.pk,
        },
    )


def _upload(
    api_client,
    obj,
    filename="test.txt",
    content=b"file content",
    visibility=None,
    content_type=None,
    secret=None,
):
    """Upload a file to an object, optionally naming a visibility tier."""
    data = {"file": SimpleUploadedFile(filename, content, content_type=content_type)}
    if visibility:
        data["json"] = json.dumps({"visibility": visibility})

    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    if secret:
        headers["X-Evan-Secret"] = secret

    return api_client.post(_file_url(obj), data, headers=headers, format="multipart")


@pytest.mark.api
@pytest.mark.django_db
class TestUploaderConfiguration:
    """The uploader configuration is enforced."""

    def test_max_files_is_enforced(self, api_client, t_event, t_event_manager):
        """A uploader capped at one file refuses a second upload."""
        content = ContentFactory(event=t_event, config={"file_uploader": {"max_files": 1}})
        api_client.force_authenticate(user=t_event_manager)

        first = _upload(api_client, content, "file1.txt")
        second = _upload(api_client, content, "file2.txt")

        assert first.status_code == status.CREATED, first.data
        assert second.status_code == status.BAD_REQUEST, second.data

    def test_default_max_files_is_one(self, api_client, t_event, t_event_manager):
        """A uploader without an explicit maximum accepts a single file."""
        content = ContentFactory(event=t_event, config={"file_uploader": {}})
        api_client.force_authenticate(user=t_event_manager)

        first = _upload(api_client, content, "file1.txt")
        second = _upload(api_client, content, "file2.txt")

        assert first.status_code == status.CREATED, first.data
        assert second.status_code == status.BAD_REQUEST, second.data

    def test_visibility_not_allowed_is_refused(self, api_client, t_event, t_event_manager):
        """A tier outside the uploader's allowed set is refused."""
        content = ContentFactory(
            event=t_event,
            config={"file_uploader": {"allowed_visibility": ["attendees"]}},
        )
        api_client.force_authenticate(user=t_event_manager)

        response = _upload(api_client, content, "file.txt", visibility="public")

        assert response.status_code == status.BAD_REQUEST, response.data

    def test_default_visibility_is_applied(self, api_client, t_event, t_event_manager):
        """An upload that names no tier gets the uploader's default tier."""
        content = ContentFactory(
            event=t_event,
            config={"file_uploader": {"default_visibility": "organizers"}},
        )
        api_client.force_authenticate(user=t_event_manager)

        response = _upload(api_client, content, "file.txt")

        assert response.status_code == status.CREATED, response.data
        assert response.data["visibility"] == File.ORGANIZERS

    def test_accepted_types_are_enforced(self, api_client, t_event, t_event_manager):
        """A file whose type is not accepted is refused."""
        content = ContentFactory(
            event=t_event,
            config={"file_uploader": {"accept": ".pdf"}},
        )
        api_client.force_authenticate(user=t_event_manager)

        refused = _upload(api_client, content, "file.txt")
        accepted = _upload(api_client, content, "file.pdf")

        assert refused.status_code == status.BAD_REQUEST, refused.data
        assert accepted.status_code == status.CREATED, accepted.data

    def test_viewset_max_files_is_enforced(self, api_client, t_event, t_event_manager):
        """A viewset's declared file cap is honoured."""
        paper = PaperFactory(event=t_event)
        api_client.force_authenticate(user=t_event_manager)

        for index in range(29):
            response = _upload(api_client, paper, f"file{index}.pdf")
            assert response.status_code == status.CREATED, response.data

        response = _upload(api_client, paper, "file29.pdf")
        assert response.status_code == status.CREATED, response.data

        response = _upload(api_client, paper, "file30.pdf")
        assert response.status_code == status.BAD_REQUEST, response.data


@pytest.mark.api
@pytest.mark.django_db
class TestSecretScopedFileManagement:
    """A session's secret manages that session's files, and nothing else."""

    def test_secret_holder_may_list_its_session_files(self, api_client, db):
        """The holder of a session's secret may list that session's files."""
        session = SessionFactory()
        File.objects.create(content_object=session, visibility=File.ORGANIZERS, file="session/slides.pdf")

        response = api_client.get(_file_url(session), headers={"X-Evan-Secret": session.secret})

        assert response.status_code == status.OK, response.data
        assert len(response.data) == 1

    def test_anonymous_holder_without_secret_is_refused(self, api_client, db):
        """Without the secret, the same request is refused."""
        session = SessionFactory()
        File.objects.create(content_object=session, visibility=File.ORGANIZERS, file="session/slides.pdf")

        response = api_client.get(_file_url(session))

        assert response.status_code == status.FORBIDDEN, response.data

    def test_foreign_secret_is_refused(self, api_client, db):
        """Another session's secret does not open this session's files."""
        session = SessionFactory()
        other_session = SessionFactory()

        response = api_client.get(_file_url(session), headers={"X-Evan-Secret": other_session.secret})

        assert response.status_code == status.FORBIDDEN, response.data

    def test_secret_holder_may_upload_to_its_session(self, api_client, db):
        """The holder of a session's secret may attach a file to that session."""
        session = SessionFactory()

        response = _upload(api_client, session, "slides.pdf", visibility="attendees", secret=session.secret)

        assert response.status_code == status.CREATED, response.data
        assert response.data["visibility"] == File.ATTENDEES

    def test_foreign_secret_cannot_upload_to_another_session(self, api_client, db):
        """A foreign secret grants no upload rights on another session."""
        session = SessionFactory()
        other_session = SessionFactory()

        response = _upload(api_client, session, "slides.pdf", secret=other_session.secret)

        assert response.status_code == status.FORBIDDEN, response.data

    def test_secret_holder_may_delete_its_session_file(self, api_client, db):
        """The holder of a session's secret may remove that session's file."""
        session = SessionFactory()
        file = File.objects.create(content_object=session, visibility=File.ATTENDEES, file="session/slides.pdf")
        url = reverse(
            "v1:file-detail",
            kwargs={
                "parent_lookup_content_type_id": file.content_type_id,
                "parent_lookup_object_id": file.object_id,
                "pk": file.pk,
            },
        )

        response = api_client.delete(url, headers={"X-Evan-Secret": session.secret})

        assert response.status_code == status.NO_CONTENT, response.data


@pytest.mark.api
@pytest.mark.django_db
class TestFileSerialization:
    """The file API exposes the visibility tier, not the old binary flag."""

    def test_created_file_round_trips_its_visibility(self, api_client, t_event, t_event_manager):
        """A created file returns its tier and its own URL."""
        content = ContentFactory(event=t_event)
        api_client.force_authenticate(user=t_event_manager)

        response = _upload(api_client, content, "file.pdf", visibility="organizers")

        assert response.status_code == status.CREATED, response.data
        assert response.data["visibility"] == File.ORGANIZERS
        assert response.data["self"].endswith(f"/files/{response.data['id']}/")
        assert "type" not in response.data

    def test_listing_exposes_the_visibility(self, api_client, t_event, t_event_manager):
        """A listing exposes each file's tier."""
        content = ContentFactory(event=t_event)
        File.objects.create(content_object=content, visibility=File.PUBLIC, file="content/public.pdf")
        api_client.force_authenticate(user=t_event_manager)

        response = api_client.get(_file_url(content))

        assert response.status_code == status.OK, response.data
        assert {entry["visibility"] for entry in response.data} == {File.PUBLIC}
