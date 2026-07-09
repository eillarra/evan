"""Base classes for PDF generation using WeasyPrint.

This module provides the foundation for generating PDF documents using
HTML templates and CSS stylesheets. All PDF makers should inherit from
BasePdfMaker to ensure consistency across the application.
"""

import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template import engines
from django.utils import timezone
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration


class PdfResponse(HttpResponse):
    """HTTP response for PDF documents.

    Handles Content-Type and Content-Disposition headers for proper
    PDF delivery in the browser or as a download.
    """

    def __init__(self, filename: str, as_attachment: bool = False):
        """Initialize PDF response.

        :param filename: Name of the PDF file for download.
        :param as_attachment: If True, forces download; if False, displays inline.
        """
        super().__init__(content_type="application/pdf")
        disposition = "attachment" if as_attachment else "inline"
        self["Content-Disposition"] = f'{disposition}; filename="{filename}"'


class BasePdfMaker:
    """Base class for PDF document generators.

    Provides template rendering with WeasyPrint, custom fonts via CSS,
    and consistent styling across all PDF documents.

    Subclasses should:
    1. Set template_name for the document template
    2. Override get_context_data() to provide template context
    3. Optionally customize base_css for additional stylesheets

    Templates are loaded from site/templates/pdf/documents/.
    """

    # Override in subclasses
    template_name: str = ""
    base_css: list[str] = ["css/pdf.css"]

    def __init__(self, *, filename: str, as_attachment: bool = False):
        """Initialize PDF maker.

        :param filename: Name of the PDF file.
        :param as_attachment: Whether to force download.
        """
        self._response = PdfResponse(filename=filename, as_attachment=as_attachment)
        self._context: dict = {}

    def get_context_data(self) -> dict:
        """Get template context data.

        Includes common context like current date, logo path, and date format.

        :returns: Context dictionary for template rendering.
        """
        return {
            "current_date": timezone.now(),
            "logo_path": self.get_logo_path(),
            "date_format": settings.DATE_FORMAT,
            **self._context,
        }

    @staticmethod
    def markdown_to_html(text: str) -> str:
        """Convert markdown text to HTML.

        :param text: Markdown text to convert.
        :returns: HTML string.
        """
        if not text:
            return ""
        from markdown import markdown

        return markdown(text)

    def get_logo_path(self) -> str:
        """Get absolute path to the UGent logo.

        Tries to find the logo in static files. Falls back to STATIC_ROOT
        in development or production.

        :returns: Absolute path to logo file for WeasyPrint.
        """
        logo_file = finders.find("images/ugent.svg")
        if logo_file:
            if isinstance(logo_file, list):
                logo_file = logo_file[0]
            return str(Path(logo_file))
        return str(Path(settings.STATIC_ROOT) / "images" / "ugent.svg")

    def get_css_files(self) -> list[Path]:
        """Get list of CSS files for styling.

        Finds CSS files in static files. Uses STATIC_ROOT in development
        or production.

        :returns: List of absolute paths to CSS files.
        """
        css_files = []
        for css_path in self.base_css:
            found = finders.find(css_path)
            if found:
                if isinstance(found, list):
                    found = found[0]
                css_files.append(Path(found))
            else:
                css_files.append(Path(settings.STATIC_ROOT) / css_path)
        return css_files

    def get_font_path(self, font_filename: str) -> str:
        """Get absolute path to a font file.

        :param font_filename: Name of the font file (e.g., 'ugentpannotext-normal-web.ttf').
        :returns: Absolute path to font file for WeasyPrint.
        """
        font_path = finders.find(f"fonts/{font_filename}")
        if font_path:
            if isinstance(font_path, list):
                font_path = font_path[0]
            return str(Path(font_path))
        return str(Path(settings.STATIC_ROOT) / "fonts" / font_filename)

    def render_html(self) -> str:
        """Render HTML template with context.

        Uses Django's template loader to render templates from
        site/templates/pdf/documents/. Templates can use all Django
        template features including inheritance, tags, and filters.

        :returns: Rendered HTML string.
        """
        # Get the Django template engine
        engine = engines["django"]
        template = engine.get_template(f"pdf/documents/{self.template_name}")
        return template.render(self.get_context_data())

    def generate_pdf(self) -> bytes:
        """Generate PDF from HTML template.

        Applies CSS stylesheets and renders to PDF using WeasyPrint.
        Supports custom fonts via @font-face in CSS.

        :returns: PDF document bytes.
        """
        html_content = self.render_html()

        # Font configuration for @font-face support
        font_config = FontConfiguration()
        css_files = self.get_css_files()
        stylesheets = []

        for css_file in css_files:
            if css_file.exists():
                # Read CSS content and resolve relative font paths to absolute paths
                css_content = css_file.read_text()
                css_content = self._resolve_font_paths(css_content, css_file.parent)
                stylesheets.append(CSS(string=css_content, font_config=font_config))

        return HTML(string=html_content).write_pdf(stylesheets=stylesheets, font_config=font_config)

    def _resolve_font_paths(self, css_content: str, css_dir: Path) -> str:
        """Resolve relative font paths in CSS to absolute paths.

        :param css_content: CSS content with relative font URLs.
        :param css_dir: Directory containing the CSS file.
        :returns: CSS content with absolute font file URLs.
        """
        # Match url() references in @font-face src properties
        pattern = r"(@font-face[^}]*src:\s*url\(['\"]?)([^'\")\s]+)(['\"]?\))"

        def replace_url(match):
            prefix = match.group(1)
            url = match.group(2)
            suffix = match.group(3)

            # Only process relative URLs (not http://, https://, data:, etc.)
            if not url.startswith(("http://", "https://", "data:", "file://")):
                # Resolve relative path from CSS file location
                font_path = (css_dir / url).resolve()
                if font_path.exists():
                    return f"{prefix}file://{font_path}{suffix}"
            return match.group(0)

        return re.sub(pattern, replace_url, css_content, flags=re.DOTALL)

    def make_pdf(self):
        """Generate PDF and write to response.

        This method should be called by subclasses in __init__ to
        populate the response with the generated PDF.
        """
        pdf_bytes = self.generate_pdf()
        self._response.write(pdf_bytes)

    @property
    def response(self) -> HttpResponse:
        """Get the PDF response object.

        :returns: HttpResponse with PDF content.
        """
        return self._response
