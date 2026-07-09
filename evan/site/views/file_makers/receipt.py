"""Receipt and Invoice PDF makers for event registrations using WeasyPrint."""

from evan.models.registrations import Registration
from evan.services.pdf.base import BasePdfMaker


class ReceiptPdfMaker(BasePdfMaker):
    """Generate receipt PDFs for paid registrations using WeasyPrint.

    Receipts are only generated for registrations that:
    - Are fully paid (saldo >= 0)
    - Have actual credit card payments (paid > 0)

    Coupon-only registrations don't get receipts.
    """

    template_name = "receipt.html"

    def __init__(self, *, registration: Registration, filename: str, as_attachment: bool = False):
        """Initialize receipt maker.

        :param registration: The registration to generate a receipt for.
        :param filename: Name of the PDF file.
        :param as_attachment: Whether to force download.
        """
        super().__init__(filename=filename, as_attachment=as_attachment)
        self.registration = registration
        self.make_pdf()

    def get_context_data(self) -> dict:
        """Build template context with registration data.

        :returns: Context dictionary for template rendering.
        """
        context = super().get_context_data()
        context.update(
            {
                "registration": self.registration,
                "signature_html": self.markdown_to_html(self.registration.event.signature),
            }
        )
        return context


class InvoicePdfMaker(ReceiptPdfMaker):
    """Generate invoice PDFs for paid registrations using WeasyPrint.

    Invoices are identical to receipts in content but use "Invoice" as the
    document title. They are intended for admin use only.
    """

    template_name = "invoice.html"
