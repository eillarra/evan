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

from evan.models import File, Session
from tests._factories import (
    ContentFactory,
    PaperFactory,
    RegistrationFactory,
    SessionFactory,
    SubsessionFactory,
    UserFactory,
)


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


def _file_detail_url(file: File) -> str:
    """Return the detail URL of a file."""
    return reverse(
        "v1:file-detail",
        kwargs={
            "parent_lookup_content_type_id": file.content_type_id,
            "parent_lookup_object_id": file.object_id,
            "pk": file.pk,
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

    def test_model_file_cap_is_enforced(self, api_client, t_event, t_event_manager):
        """A paper accepts 30 files and refuses the 31st."""
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

        response = api_client.delete(_file_detail_url(file), headers={"X-Evan-Secret": session.secret})

        assert response.status_code == status.NO_CONTENT, response.data

    def test_registration_secret_cannot_upload(self, api_client, t_event):
        """A registration's delegated-payment link does not create a file."""
        registration = RegistrationFactory(event=t_event, user=UserFactory(), is_accepted=True)

        response = _upload(api_client, registration, "invoice.pdf", secret=registration.secret)

        assert response.status_code == status.FORBIDDEN, response.data
        assert not File.objects.filter(
            content_type=ContentType.objects.get_for_model(registration), object_id=registration.pk
        ).exists()

    def test_paper_secret_cannot_upload(self, api_client, db):
        """A paper's editing link does not create a file on the paper."""
        paper = PaperFactory()

        response = _upload(api_client, paper, "draft.pdf", visibility=File.ORGANIZERS, secret=paper.secret)

        assert response.status_code == status.FORBIDDEN, response.data
        assert not File.objects.filter(
            content_type=ContentType.objects.get_for_model(paper), object_id=paper.pk
        ).exists()

    def test_paper_secret_cannot_delete(self, api_client, db):
        """A paper's editing link does not remove the paper's files either."""
        paper = PaperFactory()
        file = File.objects.create(content_object=paper, visibility=File.ORGANIZERS, file="paper/draft.pdf")

        response = api_client.delete(_file_detail_url(file), headers={"X-Evan-Secret": paper.secret})

        assert response.status_code == status.FORBIDDEN, response.data

    def test_non_ascii_secret_is_refused(self, api_client, db):
        """A crafted header is refused, not compared byte by byte in a way that raises."""
        session = SessionFactory()
        File.objects.create(content_object=session, visibility=File.ORGANIZERS, file="session/slides.pdf")

        response = api_client.get(_file_url(session), headers={"X-Evan-Secret": "sécret"})

        assert response.status_code == status.FORBIDDEN, response.data

    def test_subsession_secret_cannot_list(self, api_client, db):
        """A subsession secret does not open a file collection it cannot own."""
        subsession = SubsessionFactory()

        response = api_client.get(_file_url(subsession), headers={"X-Evan-Secret": subsession.secret})

        assert response.status_code == status.FORBIDDEN, response.data


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


@pytest.mark.api
@pytest.mark.django_db
class TestMissingContentObject:
    """A file collection hung off an object that does not exist."""

    @staticmethod
    def _url(object_id: int | str) -> str:
        return reverse(
            "v1:file-list",
            kwargs={
                "parent_lookup_content_type_id": ContentType.objects.get_for_model(Session).id,
                "parent_lookup_object_id": object_id,
            },
        )

    def test_anonymous_visitor_is_refused_without_probing(self, api_client, db):
        """An anonymous request is refused before the object is looked up."""
        response = api_client.get(self._url(999_999))

        assert response.status_code == status.FORBIDDEN, response.data

    def test_anonymous_visitor_with_a_secret_learns_nothing_either(self, api_client, db):
        """A bad secret gets the same answer for a missing object and a foreign one."""
        response = api_client.get(self._url(999_999), headers={"X-Evan-Secret": "not-a-secret"})

        assert response.status_code == status.FORBIDDEN, response.data

    def test_missing_object_is_not_found(self, api_client, t_event_manager):
        """A signed-in requester learns the object is gone, not that it crashed."""
        api_client.force_authenticate(user=t_event_manager)

        response = api_client.get(self._url(999_999))

        assert response.status_code == status.NOT_FOUND, response.data

    def test_object_id_that_is_not_a_number_is_not_found(self, api_client, t_event_manager):
        """The nested route accepts any object id, including ones no lookup can use."""
        api_client.force_authenticate(user=t_event_manager)

        response = api_client.get(self._url("not-an-id"))

        assert response.status_code == status.NOT_FOUND, response.data


@pytest.mark.api
@pytest.mark.django_db
class TestFileUpdates:
    """Editing a file is not an upload."""

    def test_description_can_be_edited_at_the_file_cap(self, api_client, t_event, t_event_manager):
        """The upload cap does not block editing a description once the object is full."""
        content = ContentFactory(event=t_event, config={"file_uploader": {"max_files": 1}})
        file = File.objects.create(content_object=content, visibility=File.ATTENDEES, file="content/one.pdf")
        api_client.force_authenticate(user=t_event_manager)

        response = api_client.patch(_file_detail_url(file), {"description": "Final version"}, format="multipart")

        assert response.status_code == status.OK, response.data
        assert response.data["description"] == "Final version"

    def test_tier_outside_the_uploader_config_is_refused_on_update(self, api_client, t_event, t_event_manager):
        """A patch cannot move a file to a tier the uploader forbids."""
        content = ContentFactory(event=t_event, config={"file_uploader": {"allowed_visibility": ["attendees"]}})
        file = File.objects.create(content_object=content, visibility=File.ATTENDEES, file="content/one.pdf")
        api_client.force_authenticate(user=t_event_manager)

        response = api_client.patch(_file_detail_url(file), {"visibility": File.PUBLIC}, format="multipart")

        assert response.status_code == status.BAD_REQUEST, response.data

    def test_allowed_tier_can_be_patched(self, api_client, t_event, t_event_manager):
        """A patch inside the allowed set goes through."""
        content = ContentFactory(
            event=t_event, config={"file_uploader": {"allowed_visibility": ["attendees", "organizers"]}}
        )
        file = File.objects.create(content_object=content, visibility=File.ATTENDEES, file="content/one.pdf")
        api_client.force_authenticate(user=t_event_manager)

        response = api_client.patch(_file_detail_url(file), {"visibility": File.ORGANIZERS}, format="multipart")

        assert response.status_code == status.OK, response.data
        assert response.data["visibility"] == File.ORGANIZERS
