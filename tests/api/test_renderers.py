"""Tests for API renderers."""

import pytest
from django.test import RequestFactory
from rest_framework.request import Request
from rest_framework.views import APIView

from evan.api.renderers import NoFormBrowsableAPIRenderer


class DummyView(APIView):
    """Dummy view for testing."""

    pass


@pytest.mark.django_db
class TestNoFormBrowsableAPIRenderer:
    """Test the NoFormBrowsableAPIRenderer."""

    def test_get_rendered_html_form_returns_none(self):
        """Test that get_rendered_html_form returns None."""
        renderer = NoFormBrowsableAPIRenderer()
        result = renderer.get_rendered_html_form()
        assert result is None

    def test_get_filter_form_returns_none(self):
        """Test that get_filter_form returns None."""
        renderer = NoFormBrowsableAPIRenderer()
        request = RequestFactory().get("/")
        drf_request = Request(request)
        view = DummyView()

        result = renderer.get_filter_form({}, view, drf_request)
        assert result is None

    def test_inherits_from_browsable_api_renderer(self):
        """Test that NoFormBrowsableAPIRenderer inherits from BrowsableAPIRenderer."""
        from rest_framework.renderers import BrowsableAPIRenderer

        renderer = NoFormBrowsableAPIRenderer()
        assert isinstance(renderer, BrowsableAPIRenderer)

    def test_has_correct_format(self):
        """Test that the renderer has the correct format."""
        renderer = NoFormBrowsableAPIRenderer()
        assert renderer.format == "api"
