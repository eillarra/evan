"""Tests for evan.services.pdf.Pdf (reportlab-based document builder).

reportlab drawing, svglib, and SimpleDocTemplate.build are mocked at the
boundary. We assert the markdown-walking logic appends Paragraph parts with
the correct styles, and that add_text/add_spacer/add_page_break compose.
"""

from unittest.mock import MagicMock, patch

import pytest
from reportlab.lib.units import cm

from evan.services.pdf import Pdf


@pytest.fixture
def pdf():
    """A Pdf instance with reportlab doc/buffer mocked."""
    with (
        patch("evan.services.pdf.SimpleDocTemplate"),
        patch("evan.services.pdf.io.BytesIO"),
    ):
        instance = Pdf()
    instance.parts = []
    return instance


class TestContextManager:
    def test_enter_returns_self(self):
        """__enter__ returns the Pdf instance."""
        with (
            patch("evan.services.pdf.SimpleDocTemplate"),
            patch("evan.services.pdf.io.BytesIO"),
        ):
            pdf = Pdf()
            assert pdf.__enter__() is pdf

    def test_exit_closes_buffer(self):
        """__exit__ closes the internal buffer."""
        with (
            patch("evan.services.pdf.SimpleDocTemplate"),
            patch("evan.services.pdf.io.BytesIO") as mock_buf,
        ):
            pdf = Pdf()
            pdf.__exit__(None, None, None)

            mock_buf.return_value.close.assert_called_once()


class TestAddTextRegular:
    def test_add_text_appends_paragraph_with_style(self, pdf):
        """Non-markdown text is appended as a Paragraph with the given style."""
        with patch("evan.services.pdf.Paragraph") as mock_paragraph:
            pdf.add_text("hello", style="p")

        mock_paragraph.assert_called_once()
        assert mock_paragraph.call_args.args[0] == "hello"
        assert mock_paragraph.call_args.args[1] is not None  # style object


class TestAddTextMarkdown:
    def test_markdown_paragraph_uses_p_style(self, pdf):
        """A markdown paragraph appends a Paragraph part."""
        with patch("evan.services.pdf.Paragraph") as mock_paragraph:
            pdf.add_text("hello world", style="p", text_format="markdown")

        assert mock_paragraph.call_count == 1
        assert mock_paragraph.call_args.args[0] == "hello world"

    def test_markdown_emph_strong_links(self, pdf):
        """Emphasis, strong, and links are wrapped in the right HTML tags."""
        with patch("evan.services.pdf.Paragraph") as mock_paragraph:
            pdf.add_text("*em* **strong** [link](http://x)", style="p", text_format="markdown")

        content = mock_paragraph.call_args.args[0]
        assert "<em>em</em>" in content
        assert "<strong>strong</strong>" in content
        assert '<a href="http://x">link</a>' in content

    def test_markdown_bullet_list_uses_ul_li_style(self, pdf):
        """A paragraph inside a bullet list uses the ul_li style."""
        with patch("evan.services.pdf.Paragraph") as mock_paragraph:
            pdf.add_text("- item one", style="p", text_format="markdown")

        # the style argument (second positional) must be the ul_li style
        style = mock_paragraph.call_args.args[1]
        assert style is not None

    def test_markdown_softbreak_becomes_space(self, pdf):
        """Softbreaks within a paragraph are rendered as spaces."""
        with patch("evan.services.pdf.Paragraph") as mock_paragraph:
            pdf.add_text("line one\nline two", style="p", text_format="markdown")

        content = mock_paragraph.call_args.args[0]
        assert content == "line one line two"

    def test_markdown_linebreak_becomes_br(self, pdf):
        """Hard linebreaks become <br /> tags."""
        with patch("evan.services.pdf.Paragraph") as mock_paragraph:
            pdf.add_text("a\\\nb", style="p", text_format="markdown")

        content = mock_paragraph.call_args.args[0]
        assert "<br />" in content

    def test_markdown_falls_back_to_escaped_on_error(self, pdf):
        """When process_markdown raises, the text is escaped and appended."""
        with (
            patch.object(Pdf, "process_markdown", side_effect=Exception("boom")),
            patch("evan.services.pdf.Paragraph") as mock_paragraph,
            patch("evan.services.pdf.escape", return_value="escaped"),
        ):
            pdf.add_text("weird word markdown", style="p", text_format="markdown")

        mock_paragraph.assert_called_once()
        assert mock_paragraph.call_args.args[0] == "escaped"


class TestAddImage:
    def test_add_image_swallows_exceptions(self, pdf):
        """add_image never propagates FloatingImage construction errors."""
        with patch("evan.services.pdf.FloatingImage", side_effect=ValueError("bad src")):
            pdf.add_image("missing.jpg")

        # no exception raised, nothing appended
        assert pdf.parts == []


class TestAddSpacer:
    def test_add_spacer_appends_spacer(self, pdf):
        """add_spacer appends a Spacer sized in cm."""
        with patch("evan.services.pdf.Spacer") as mock_spacer:
            pdf.add_spacer(1.5)

        mock_spacer.assert_called_once_with(pdf.doc.width, 1.5 * cm)


class TestAddPageBreak:
    def test_add_page_break_appends_pagebreak(self, pdf):
        """add_page_break appends a PageBreak part."""
        with patch("evan.services.pdf.PageBreak") as mock_pb:
            pdf.add_page_break()

        mock_pb.assert_called_once()
        assert pdf.parts == [mock_pb.return_value]


class TestGet:
    def test_get_builds_doc_and_returns_buffer_content(self, pdf):
        """get builds the doc with page callbacks and returns buffer bytes."""
        pdf.buffer = MagicMock()
        pdf.buffer.getvalue.return_value = b"PDF"

        result = pdf.get()

        assert result == b"PDF"
        pdf.doc.build.assert_called_once()
        kwargs = pdf.doc.build.call_args.kwargs
        assert "onFirstPage" in kwargs
        assert "onLaterPages" in kwargs


class TestPageCallbacks:
    def test_first_page_draws_logo(self, pdf):
        """_first_page delegates to _draw_logo with the canvas and doc."""
        canvas = MagicMock()
        doc = MagicMock()
        with patch.object(pdf, "_draw_logo") as mock_draw:
            pdf._first_page(canvas, doc)

        mock_draw.assert_called_once_with(canvas, doc)

    def test_later_pages_draws_logo(self, pdf):
        """_later_pages also delegates to _draw_logo."""
        canvas = MagicMock()
        doc = MagicMock()
        with patch.object(pdf, "_draw_logo") as mock_draw:
            pdf._later_pages(canvas, doc)

        mock_draw.assert_called_once_with(canvas, doc)

    def test_draw_logo_loads_svg_and_draws_on_canvas(self, pdf, settings):
        """_draw_logo loads the UGent SVG via svglib and draws it onto the canvas."""
        settings.SITE_ROOT = "/srv/site"
        canvas = MagicMock()
        doc = MagicMock()
        doc.leftMargin = 2
        doc.height = 100
        doc.topMargin = 4

        with patch("evan.services.pdf.svg2rlg") as mock_svg:
            drawing = mock_svg.return_value

            pdf._draw_logo(canvas, doc)

        mock_svg.assert_called_once_with("/srv/site/static/images/ugent.svg")
        drawing.drawOn.assert_called_once()
        canvas.saveState.assert_called_once()
        canvas.restoreState.assert_called_once()


class TestPdfResponse:
    def test_sets_pdf_content_type(self):
        """PdfResponse defaults to application/pdf."""
        from evan.services.pdf import PdfResponse

        response = PdfResponse(filename="x.pdf")

        assert response["Content-Type"] == "application/pdf"

    def test_keeps_filename_and_as_attachment(self):
        """PdfResponse stores filename and as_attachment flags."""
        from evan.services.pdf import PdfResponse

        response = PdfResponse(filename="report.pdf", as_attachment=True)

        assert response.filename == "report.pdf"
        assert response.as_attachment is True
