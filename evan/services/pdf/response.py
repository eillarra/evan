"""HTTP response for PDF documents.

Shared by both PDF stacks (WeasyPrint document makers and the ReportLab badge
maker) so neither defines its own response class. Lives inside the
``evan.services.pdf`` package for discoverability; importing it triggers the
package ``__init__`` (and thus ReportLab), which is acceptable in this app.
"""

from django.http import HttpResponse
from django.utils.text import slugify


def _safe_filename(filename: str) -> str:
    """Slugify a filename for use in ``Content-Disposition`` while keeping the extension.

    The stem is slugified to an ASCII-safe slug (spaces, accents and other
    unsafe characters removed) so browsers never need RFC 5987 encoding; the
    extension is preserved verbatim.

    :param filename: The proposed filename, possibly with unsafe characters.
    :returns: A safe filename such as ``receipt-jane-doe-<uuid>.pdf``.
    """
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
    else:
        stem, ext = filename, ""
    stem = slugify(stem) or "document"
    return f"{stem}.{ext}" if ext else stem


class PdfResponse(HttpResponse):
    """HTTP response carrying a PDF document.

    Sets the ``Content-Type`` to ``application/pdf`` and a slugified
    ``Content-Disposition`` filename so the browser either displays the
    document inline or downloads it, depending on ``as_attachment``.

    The (sanitized) ``filename`` and ``as_attachment`` values are also kept as
    instance attributes for convenience.

    :param filename: Name of the PDF file for the download. Slugified for safety.
    :param as_attachment: If True, forces download; if False, displays inline.
    """

    def __init__(self, filename: str, as_attachment: bool = False) -> None:
        filename = _safe_filename(filename)
        super().__init__(content_type="application/pdf")
        self.filename = filename
        self.as_attachment = as_attachment
        disposition = "attachment" if as_attachment else "inline"
        self["Content-Disposition"] = f'{disposition}; filename="{filename}"'
