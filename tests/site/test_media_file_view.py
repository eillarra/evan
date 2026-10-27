"""
Tests for MediaFileView cookie handling.
"""

from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from evan.models.rel.files import File
from evan.site.views.files import MediaFileView
from tests._factories import RegistrationFactory, UserFactory


@pytest.mark.django_db
class TestMediaFileViewCookieHandling:
    """Test that MediaFileView properly handles cookies."""

    @patch("evan.site.views.files.get_s3_response")
    def test_cookies_removed_from_private_file_response(self, mock_s3_response):
        """Test that cookies are removed from private file responses."""
        # Setup
        user = UserFactory()

        # Mock the S3 response
        mock_response = Mock()
        mock_response.raw = b"fake file content"
        mock_response.headers = {"Content-Length": "17", "Content-Type": "text/plain"}
        mock_s3_response.return_value = mock_response

        # Create a mock file object
        mock_file = Mock(spec=File)
        mock_file.file.name = "private/test.txt"
        mock_file.s3_object_key = "private/test.txt"
        mock_file.is_public = False
        mock_file.is_accessible_by_user.return_value = True

        # Create request and view
        request = RequestFactory().get("/media/private/test.txt")
        request.user = user

        view = MediaFileView()
        view.object = mock_file

        # Execute
        response = view.get(request)

        # Assert
        assert isinstance(response, HttpResponse)
        assert len(response.cookies) == 0  # No cookies should be present
        assert response["Cache-Control"] == "private, no-cache"  # Private file cache header

    @patch("evan.site.views.files.get_s3_response")
    def test_cookies_removed_from_public_file_response(self, mock_s3_response):
        """Test that cookies are removed from public file responses and cache headers are set."""
        # Setup
        user = UserFactory()

        # Mock the S3 response
        mock_response = Mock()
        mock_response.raw = b"fake file content"
        mock_response.headers = {"Content-Length": "17", "Content-Type": "image/jpeg"}
        mock_s3_response.return_value = mock_response

        # Create a mock public file object
        mock_file = Mock(spec=File)
        mock_file.file.name = "public/image.jpg"
        mock_file.s3_object_key = "public/image.jpg"
        mock_file.is_public = True
        mock_file.is_accessible_by_user.return_value = True

        # Create request and view
        request = RequestFactory().get("/media/public/image.jpg")
        request.user = user

        view = MediaFileView()
        view.object = mock_file

        # Execute
        response = view.get(request)

        # Assert
        assert isinstance(response, HttpResponse)
        assert len(response.cookies) == 0  # No cookies should be present
        assert response["Cache-Control"] == "public, max-age=3600"  # Public file cache header

    def test_view_has_proper_methods(self):
        """Test that the view has the expected methods."""
        view = MediaFileView()
        assert hasattr(view, "get")
        assert callable(view.get)
        assert hasattr(view, "dispatch")
        assert callable(view.dispatch)
        assert hasattr(view, "get_object")
        assert callable(view.get_object)

    def test_middleware_respects_no_cookies_flag(self):
        """Test that NoCookiesMiddleware respects the _no_cookies flag."""
        from django.http import HttpResponse

        from evan.middleware import NoCookiesMiddleware

        # Mock get_response that adds a cookie
        def mock_get_response(request):
            response = HttpResponse("test")
            response.set_cookie("test_cookie", "value")
            response._no_cookies = True  # type: ignore
            return response

        # Create middleware and test request
        middleware = NoCookiesMiddleware(mock_get_response)
        request = Mock()

        # Execute
        response = middleware(request)

        # Assert cookies were cleared
        assert len(response.cookies) == 0
        assert hasattr(response, "_no_cookies")
        assert response._no_cookies is True

    @pytest.mark.django_db
    class TestMediaFileViewAccess:
        """Access control behaviour of MediaFileView.

        Anonymous users are redirected to the login page; authenticated users
        without access get a 403; accepted attendees get the file.
        """

        @pytest.fixture(autouse=True)
        def media_root(self, settings, tmp_path):
            """Redirect media storage to a temp directory so tests never touch real files."""
            settings.MEDIA_ROOT = tmp_path / "media"

        @staticmethod
        def _create_event_file(t_event, visibility=File.ATTENDEES):
            """Create a File attached to the given event."""
            from django.core.files.base import ContentFile

            return File.objects.create(
                content_object=t_event,
                visibility=visibility,
                file=ContentFile(b"proceedings", name="event/proceedings.pdf"),
            )

        def test_anonymous_user_redirects_to_login(self, client, t_event):
            """Anonymous users are redirected to the login page instead of getting a 403."""
            file = self._create_event_file(t_event)

            response = client.get(f"/media/{file.file.name}")

            assert response.status_code == 302
            assert "/u/login/" in response["Location"]
            assert f"next=/media/{file.file.name}" in response["Location"]

        def test_accepted_attendee_gets_file(self, client, t_event):
            """An accepted attendee can download an attendees-tier event file."""
            file = self._create_event_file(t_event)
            user = UserFactory()
            RegistrationFactory(event=t_event, user=user, is_accepted=True)
            client.force_login(user)

            with patch("evan.site.views.files.get_s3_response") as mock_s3_response:
                mock_response = Mock()
                mock_response.raw = b"proceedings"
                mock_response.headers = {"Content-Length": "11", "Content-Type": "application/pdf"}
                mock_s3_response.return_value = mock_response

                response = client.get(f"/media/{file.file.name}")

            assert response.status_code == 200
            assert response["Cache-Control"] == "private, no-cache"

        def test_pending_attendee_gets_403(self, client, db):
            """A user with a pending registration gets a 403, not the file."""
            from evan.models import Fee
            from tests._factories import EventFactory

            event = EventFactory(accept_by_default=False)
            Fee.objects.create(event=event, type="regular", value=100)
            file = self._create_event_file(event)
            user = UserFactory()
            RegistrationFactory(event=event, user=user, is_accepted=None)
            client.force_login(user)

            response = client.get(f"/media/{file.file.name}")

            assert response.status_code == 403

        def test_unregistered_user_gets_403(self, client, t_event):
            """An authenticated user without a registration gets a 403, not the file."""
            file = self._create_event_file(t_event)
            user = UserFactory()
            client.force_login(user)

            response = client.get(f"/media/{file.file.name}")

            assert response.status_code == 403

        def test_public_file_served_to_anonymous_user(self, client, t_event):
            """Public files are served without authentication."""
            file = self._create_event_file(t_event, visibility=File.PUBLIC)

            with patch("evan.site.views.files.get_s3_response") as mock_s3_response:
                mock_response = Mock()
                mock_response.raw = b"public content"
                mock_response.headers = {"Content-Length": "13", "Content-Type": "application/pdf"}
                mock_s3_response.return_value = mock_response

                response = client.get(f"/media/{file.file.name}")

            assert response.status_code == 200
            assert response["Cache-Control"] == "public, max-age=3600"

        def test_organizers_file_refused_to_attendee(self, client, t_event):
            """An accepted attendee cannot download an organizers-tier file."""
            file = self._create_event_file(t_event, visibility=File.ORGANIZERS)
            user = UserFactory()
            RegistrationFactory(event=t_event, user=user, is_accepted=True)
            client.force_login(user)

            response = client.get(f"/media/{file.file.name}")

            assert response.status_code == 403

        def test_organizers_file_served_to_event_manager(self, client, t_event):
            """An event manager can download an organizers-tier file."""
            from evan.models import Permission

            file = self._create_event_file(t_event, visibility=File.ORGANIZERS)
            user = UserFactory()
            Permission.objects.create(content_object=t_event, user=user, level=Permission.ADMIN)
            client.force_login(user)

            with patch("evan.site.views.files.get_s3_response") as mock_s3_response:
                mock_response = Mock()
                mock_response.raw = b"proceedings"
                mock_response.headers = {"Content-Length": "11", "Content-Type": "application/pdf"}
                mock_s3_response.return_value = mock_response

                response = client.get(f"/media/{file.file.name}")

            assert response.status_code == 200
            assert response["Cache-Control"] == "private, no-cache"

        def test_session_secret_unlocks_its_own_organizers_file(self, client, db):
            """A session's secret opens that session's organizers-tier file."""
            from django.core.files.base import ContentFile

            from tests._factories import SessionFactory

            session = SessionFactory()
            file = File.objects.create(
                content_object=session,
                visibility=File.ORGANIZERS,
                file=ContentFile(b"slides", name="session/slides.pdf"),
            )

            with patch("evan.site.views.files.get_s3_response") as mock_s3_response:
                mock_response = Mock()
                mock_response.raw = b"slides"
                mock_response.headers = {"Content-Length": "6", "Content-Type": "application/pdf"}
                mock_s3_response.return_value = mock_response

                response = client.get(f"/media/{file.file.name}", headers={"X-Evan-Secret": session.secret})

            assert response.status_code == 200

        def test_legacy_address_serves_the_relocated_file(self, client, t_event):
            """An address handed out before the relocation keeps resolving."""
            file = self._create_event_file(t_event, visibility=File.PUBLIC)
            legacy_path = f"/media/public/{file.file.name.removeprefix('files/')}"

            with patch("evan.site.views.files.get_s3_response") as mock_s3_response:
                mock_response = Mock()
                mock_response.raw = b"proceedings"
                mock_response.headers = {"Content-Length": "11", "Content-Type": "application/pdf"}
                mock_s3_response.return_value = mock_response

                response = client.get(legacy_path)

            assert response.status_code == 200

        def test_legacy_address_is_still_guarded(self, client, t_event):
            """The fallback grants no access the current address would not."""
            file = self._create_event_file(t_event)
            legacy_path = f"/media/public/{file.file.name.removeprefix('files/')}"

            response = client.get(legacy_path)

            assert response.status_code == 302
            assert "/u/login/" in response["Location"]

        def test_address_naming_no_file_is_not_found(self, client, db):
            """A legacy-looking address with nothing behind it is a 404."""
            assert client.get("/media/public/nowhere/really.pdf").status_code == 404

        def test_foreign_session_secret_is_refused(self, client, db):
            """Another session's secret does not open this session's file."""
            from django.core.files.base import ContentFile

            from tests._factories import SessionFactory

            session = SessionFactory()
            other_session = SessionFactory()
            file = File.objects.create(
                content_object=session,
                visibility=File.ORGANIZERS,
                file=ContentFile(b"slides", name="session/slides.pdf"),
            )

            response = client.get(f"/media/{file.file.name}", headers={"X-Evan-Secret": other_session.secret})

            assert response.status_code == 403
