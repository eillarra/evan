"""PDF makers for registration documents (receipt, invoice, invitation letter,
certificate) using WeasyPrint.

All four documents are tied to a single ``Registration`` and share the same
context shape (the registration plus its event). ``BaseRegistrationPdfMaker``
captures that commonality; concrete makers only set ``template_name`` and
``doc_slug`` (used for the default download filename). ReportLab remains in
use only for badges (precise millimetre layout).
"""

from evan.models.registrations import Registration
from evan.services.pdf.base import BasePdfMaker


class BaseRegistrationPdfMaker(BasePdfMaker):
    """Base for PDF documents generated for a single registration.

    The download filename defaults to
    ``{event.code}-{doc_slug}-{user name}-{uuid}.pdf`` so attendees get a
    meaningful, identifiable file without callers having to assemble one. The
    raw name is slugified once by ``PdfResponse`` (not here) to avoid double
    work. Pass ``filename`` explicitly to override.

    :param registration: The registration the document is generated for.
    :param filename: Name of the PDF file. Defaults to ``default_filename``.
    :param as_attachment: Whether to force download.
    """

    #: Short identifier used in the default filename (e.g. ``"receipt"``).
    doc_slug = "document"

    def __init__(
        self,
        *,
        registration: Registration,
        filename: str | None = None,
        as_attachment: bool = False,
    ) -> None:
        filename = filename or self.default_filename(registration)
        super().__init__(event=registration.event, filename=filename, as_attachment=as_attachment)
        self.registration = registration
        self.make_pdf()

    @classmethod
    def default_filename(cls, registration: Registration) -> str:
        """Build the default download filename for this document.

        :param registration: The registration the document is generated for.
        :returns: A filename like ``<event-code>-receipt-Jane Doe-<uuid>.pdf``.
            Slugified by ``PdfResponse`` at response time, not here.
        """
        parts = [registration.event.code, cls.doc_slug, registration.user.name, str(registration.uuid)]
        return "-".join(part for part in parts if part) + ".pdf"

    def get_context_data(self) -> dict:
        """Build template context with the registration.

        :returns: Context dictionary for template rendering.
        """
        context = super().get_context_data()
        context["registration"] = self.registration
        return context


class ReceiptPdfMaker(BaseRegistrationPdfMaker):
    """Generate a receipt PDF for a paid registration.

    Receipts are only generated for registrations that are fully paid and
    have actual credit card payments (``paid > 0``); coupon-only registrations
    do not get receipts.
    """

    doc_slug = "receipt"
    template_name = "receipt.html"


class InvoicePdfMaker(BaseRegistrationPdfMaker):
    """Generate an invoice PDF for a paid registration.

    Invoices mirror receipts in content but use the invoice template. They are
    intended for admin use only.
    """

    doc_slug = "invoice"
    template_name = "invoice.html"


class InvitationLetterPdfMaker(BaseRegistrationPdfMaker):
    """Generate an invitation letter PDF for a registration with a letter."""

    doc_slug = "invitation-letter"
    template_name = "invitation_letter.html"


class CertificatePdfMaker(BaseRegistrationPdfMaker):
    """Generate a certificate of attendance PDF for a registration."""

    doc_slug = "certificate"
    template_name = "certificate.html"
