"""Tests for evan.services.pdf.base.

WeasyPrint, the staticfiles finders, and the Django template engine are
mocked at the boundary. We assert our composition logic, not the libraries.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evan.services.pdf.base import BasePdfMaker, PdfResponse


class TestPdfResponse:
    def test_inline_disposition_by_default(self):
        """Without as_attachment, the response is inline."""
        response = PdfResponse(filename="doc.pdf")

        assert response["Content-Type"] == "application/pdf"
        assert response["Content-Disposition"] == 'inline; filename="doc.pdf"'

    def test_attachment_disposition_when_requested(self):
        """as_attachment=True forces a download disposition."""
        response = PdfResponse(filename="report.pdf", as_attachment=True)

        assert response["Content-Disposition"] == 'attachment; filename="report.pdf"'


class _DummyMaker(BasePdfMaker):
    template_name = "dummy.html"
    base_css = ["css/pdf.css"]


@pytest.fixture
def maker():
    """A BasePdfMaker subclass instance for testing."""
    return _DummyMaker(filename="out.pdf", as_attachment=True)


class TestGetContextData:
    def test_context_includes_common_keys_and_overrides(self, maker):
        """get_context_data merges common defaults with the provided context."""
        maker._context = {"title": "Hello"}

        with patch("evan.services.pdf.base.timezone") as mock_tz:
            mock_tz.now.return_value = "NOW"
            with patch.object(BasePdfMaker, "get_logo_path", return_value="/logo.svg"):
                context = maker.get_context_data()

        assert context["current_date"] == "NOW"
        assert context["logo_path"] == "/logo.svg"
        assert context["title"] == "Hello"


class TestMarkdownToHtml:
    def test_empty_text_returns_empty_string(self):
        """Falsy input short-circuits to an empty string."""
        assert BasePdfMaker.markdown_to_html("") == ""
        assert BasePdfMaker.markdown_to_html(None) == ""

    def test_markdown_is_converted_to_html(self):
        """A markdown string is converted to HTML by the markdown library."""
        with patch("markdown.markdown", return_value="<p>hi</p>") as mock_md:
            result = BasePdfMaker.markdown_to_html("# hi")

        assert result == "<p>hi</p>"
        mock_md.assert_called_once_with("# hi")


class TestGetLogoPath:
    def test_returns_found_static_path(self, maker):
        """When finders locate the logo, its path is returned."""
        with patch("evan.services.pdf.base.finders.find", return_value="/static/images/ugent.svg"):
            result = maker.get_logo_path()

        assert result == "/static/images/ugent.svg"

    def test_returns_list_first_element(self, maker):
        """When finders returns a list, the first element is used."""
        with patch("evan.services.pdf.base.finders.find", return_value=["/static/a.svg", "/static/b.svg"]):
            result = maker.get_logo_path()

        assert result == "/static/a.svg"

    def test_falls_back_to_static_root(self, maker, settings):
        """When finders cannot locate the logo, fall back to STATIC_ROOT."""
        settings.STATIC_ROOT = "/srv/static"
        with patch("evan.services.pdf.base.finders.find", return_value=None):
            result = maker.get_logo_path()

        assert result == str(Path("/srv/static/images/ugent.svg"))


class TestGetCssFiles:
    def test_returns_found_css_paths(self, maker):
        """Found CSS files are returned as Path objects."""
        with patch("evan.services.pdf.base.finders.find", return_value="/static/css/pdf.css"):
            files = maker.get_css_files()

        assert files == [Path("/static/css/pdf.css")]

    def test_falls_back_to_static_root_for_missing_css(self, maker, settings):
        """Missing CSS files fall back to STATIC_ROOT."""
        settings.STATIC_ROOT = "/srv/static"
        with patch("evan.services.pdf.base.finders.find", return_value=None):
            files = maker.get_css_files()

        assert files == [Path("/srv/static/css/pdf.css")]


class TestGetFontPath:
    def test_returns_found_font_path(self, maker):
        """When finders locate the font, its path is returned."""
        with patch("evan.services.pdf.base.finders.find", return_value="/static/fonts/font.ttf"):
            result = maker.get_font_path("font.ttf")

        assert result == "/static/fonts/font.ttf"

    def test_falls_back_to_static_root(self, maker, settings):
        """Missing fonts fall back to STATIC_ROOT."""
        settings.STATIC_ROOT = "/srv/static"
        with patch("evan.services.pdf.base.finders.find", return_value=None):
            result = maker.get_font_path("font.ttf")

        assert result == str(Path("/srv/static/fonts/font.ttf"))


class TestResolveFontPaths:
    def test_absolute_file_url_for_existing_relative_font(self, maker, tmp_path):
        """Relative font URLs pointing at existing files become file:// URLs."""
        font = tmp_path / "font.woff"
        font.write_text("font")
        css = "@font-face { src: url('font.woff'); }"

        result = maker._resolve_font_paths(css, tmp_path)

        assert f"file://{font.resolve()}" in result

    def test_keeps_absolute_http_urls(self, maker, tmp_path):
        """http(s)://, data:, and file:// URLs are left untouched."""
        css = "@font-face { src: url('https://example.org/font.woff'); }"

        result = maker._resolve_font_paths(css, tmp_path)

        assert result == css

    def test_keeps_nonexistent_relative_urls(self, maker, tmp_path):
        """Relative URLs pointing at missing files are left as-is."""
        css = "@font-face { src: url('missing.woff'); }"

        result = maker._resolve_font_paths(css, tmp_path)

        assert result == css


class TestRenderHtml:
    def test_renders_template_with_context(self, maker):
        """render_html delegates to the Django template engine with context."""
        fake_template = MagicMock()
        fake_template.render.return_value = "<html/>"
        fake_engine = MagicMock()
        fake_engine.get_template.return_value = fake_template

        with (
            patch("evan.services.pdf.base.engines", {"django": fake_engine}),
            patch.object(BasePdfMaker, "get_logo_path", return_value="/logo.svg"),
        ):
            result = maker.render_html()

        fake_engine.get_template.assert_called_once_with("pdf/documents/dummy.html")
        assert result == "<html/>"


class TestGeneratePdf:
    def test_generate_pdf_renders_html_and_writes_pdf(self, maker, tmp_path):
        """generate_pdf renders HTML, attaches existing CSS, and writes the PDF."""
        css_path = tmp_path / "pdf.css"
        css_path.write_text("@font-face { src: url('font.woff'); }")
        font_path = tmp_path / "font.woff"
        font_path.write_text("font")

        with (
            patch("evan.services.pdf.base.HTML") as mock_html,
            patch("evan.services.pdf.base.CSS") as mock_css,
            patch("evan.services.pdf.base.FontConfiguration") as mock_fc,
            patch.object(BasePdfMaker, "render_html", return_value="<html/>"),
            patch.object(BasePdfMaker, "get_css_files", return_value=[css_path]),
        ):
            mock_html.return_value.write_pdf.return_value = b"PDFBYTES"

            result = maker.generate_pdf()

        assert result == b"PDFBYTES"
        mock_html.assert_called_once_with(string="<html/>")
        mock_css.assert_called_once()
        mock_fc.assert_called_once()


class TestMakePdf:
    def test_make_pdf_writes_bytes_to_response(self, maker):
        """make_pdf populates the response with the generated bytes."""
        with patch.object(BasePdfMaker, "generate_pdf", return_value=b"PDFBYTES"):
            maker.make_pdf()

        assert maker.response.content == b"PDFBYTES"

    def test_response_property_returns_http_response(self, maker):
        """The response property exposes the underlying PdfResponse."""
        with patch.object(BasePdfMaker, "generate_pdf", return_value=b""):
            maker.make_pdf()

        from django.http import HttpResponse

        assert isinstance(maker.response, HttpResponse)
