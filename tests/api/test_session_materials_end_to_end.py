"""End-to-end check of the session materials flow.

Covers the whole path a material takes: an organizer attaches it to a session
in the console, the session organizer manages it through the session's secret
link, and each audience — anonymous, accepted attendee, event manager — sees
exactly the materials its tier allows.
"""

import json
from http import HTTPStatus as status
from unittest.mock import Mock, patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from evan.models import Fee, File
from evan.models.rel.permissions import Permission
from tests._factories import RegistrationFactory, SessionFactory, UserFactory


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Redirect media storage to a temp directory so tests never touch real files."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def session(db):
    """A session with an event manager and an accepted attendee."""
    session = SessionFactory()
    Fee.objects.create(event=session.event, type="regular", value=100)
    manager = UserFactory()
    Permission.objects.create(content_object=session.event, user=manager, level=Permission.ADMIN)
    attendee = UserFactory()
    RegistrationFactory(event=session.event, user=attendee, is_accepted=True)
    return session, manager, attendee


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


def _attach(api_client, obj, filename, visibility, user=None) -> str:
    """Attach a material to an object and return the created file's URL."""
    if user is not None:
        api_client.force_authenticate(user=user)

    response = api_client.post(
        _file_url(obj),
        {
            "file": SimpleUploadedFile(filename, b"content"),
            "json": json.dumps({"visibility": visibility, "description": filename}),
        },
        headers={"Content-Disposition": f"attachment; filename={filename}"},
        format="multipart",
    )
    assert response.status_code == status.CREATED, response.data
    return response.data["file"]


def _s3_response():
    """Return a mocked S3 response."""
    response = Mock()
    response.raw = b"content"
    response.headers = {"Content-Length": "7", "Content-Type": "application/pdf"}
    return response


@pytest.mark.api
@pytest.mark.django_db
class TestSessionMaterialsEndToEnd:
    """The full materials flow, from attaching to downloading."""

    def test_organizer_attaches_a_material_of_each_tier(self, api_client, session):
        """An organizer attaches one material per tier to a session."""
        session_obj, manager, _ = session

        public_url = _attach(api_client, session_obj, "public.pdf", File.PUBLIC, manager)
        attendees_url = _attach(api_client, session_obj, "attendees.pdf", File.ATTENDEES, manager)
        organizers_url = _attach(api_client, session_obj, "organizers.pdf", File.ORGANIZERS, manager)

        assert session_obj.files.count() == 3
        assert public_url != attendees_url != organizers_url

    def test_each_audience_sees_exactly_its_own_materials(self, api_client, session):
        """Anonymous, attendee and manager each see the right set of materials."""
        session_obj, manager, attendee = session
        _attach(api_client, session_obj, "public.pdf", File.PUBLIC, manager)
        _attach(api_client, session_obj, "attendees.pdf", File.ATTENDEES, manager)
        _attach(api_client, session_obj, "organizers.pdf", File.ORGANIZERS, manager)

        # The session's own listing is public and filtered per viewer.
        api_client.force_authenticate(user=None)
        api_client.credentials()
        anonymous = api_client.get(session_obj.get_api_url())
        assert anonymous.status_code == status.OK
        assert {entry["visibility"] for entry in anonymous.data["files"]} == {File.PUBLIC}

        api_client.force_authenticate(user=attendee)
        as_attendee = api_client.get(session_obj.get_api_url())
        assert {entry["visibility"] for entry in as_attendee.data["files"]} == {File.PUBLIC, File.ATTENDEES}

        api_client.force_authenticate(user=manager)
        as_manager = api_client.get(session_obj.get_api_url())
        assert {entry["visibility"] for entry in as_manager.data["files"]} == {
            File.PUBLIC,
            File.ATTENDEES,
            File.ORGANIZERS,
        }

    def test_the_management_endpoint_is_closed_to_anonymous_visitors(self, api_client, session):
        """The related-files endpoint stays a management surface."""
        session_obj, manager, _ = session
        _attach(api_client, session_obj, "public.pdf", File.PUBLIC, manager)

        api_client.force_authenticate(user=None)
        api_client.credentials()

        response = api_client.get(_file_url(session_obj))
        assert response.status_code == status.FORBIDDEN

    def test_the_download_path_honours_the_tier(self, client, session):
        """The media path serves a material to the audience its tier allows."""
        session_obj, manager, attendee = session
        public = File.objects.create(
            content_object=session_obj,
            visibility=File.PUBLIC,
            file=ContentFile(b"content", name="session/public.pdf"),
        )
        organizers = File.objects.create(
            content_object=session_obj,
            visibility=File.ORGANIZERS,
            file=ContentFile(b"content", name="session/organizers.pdf"),
        )

        with patch("evan.site.views.files.get_s3_response", return_value=_s3_response()):
            anonymous = client.get(f"/media/{public.file.name}")
            assert anonymous.status_code == status.OK

            client.force_login(attendee)
            refused = client.get(f"/media/{organizers.file.name}")
            assert refused.status_code == status.FORBIDDEN

            client.force_login(manager)
            allowed = client.get(f"/media/{organizers.file.name}")
            assert allowed.status_code == status.OK

    def test_the_session_organizer_manages_the_materials(self, api_client, session):
        """The session's secret lists, attaches and removes its own materials."""
        session_obj, _, _ = session

        api_client.force_authenticate(user=None)
        api_client.credentials()

        attached = api_client.post(
            _file_url(session_obj),
            {
                "file": SimpleUploadedFile("slides.pdf", b"content"),
                "json": json.dumps({"visibility": File.ORGANIZERS, "description": "Slides"}),
            },
            headers={
                "Content-Disposition": "attachment; filename=slides.pdf",
                "X-Evan-Secret": session_obj.secret,
            },
            format="multipart",
        )
        assert attached.status_code == status.CREATED, attached.data
        assert attached.data["visibility"] == File.ORGANIZERS

        listed = api_client.get(_file_url(session_obj), headers={"X-Evan-Secret": session_obj.secret})
        assert listed.status_code == status.OK
        assert len(listed.data) == 1

        detail_url = reverse(
            "v1:file-detail",
            kwargs={
                "parent_lookup_content_type_id": ContentType.objects.get_for_model(session_obj).id,
                "parent_lookup_object_id": session_obj.pk,
                "pk": attached.data["id"],
            },
        )
        removed = api_client.delete(detail_url, headers={"X-Evan-Secret": session_obj.secret})
        assert removed.status_code == status.NO_CONTENT
        assert session_obj.files.count() == 0

    def test_a_foreign_secret_reaches_nothing(self, api_client, session):
        """Another session's secret opens nothing on this session."""
        session_obj, _, _ = session
        other_session = SessionFactory()

        api_client.force_authenticate(user=None)
        api_client.credentials()

        listed = api_client.get(_file_url(session_obj), headers={"X-Evan-Secret": other_session.secret})
        assert listed.status_code == status.FORBIDDEN
