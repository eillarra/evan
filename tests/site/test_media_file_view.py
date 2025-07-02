"""
Tests for MediaFileView cookie handling.
"""

from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from evan.models.rel.files import File
from evan.site.views.files import MediaFileView
from tests._factories import UserFactory


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
