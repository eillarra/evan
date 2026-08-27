"""Tests default download filename generation for registration PDF makers.

``default_filename`` builds the *raw* filename (event code + doc slug + user
name + uuid). Slugification to an ASCII-safe string is the responsibility of
``PdfResponse`` (see ``tests/services/pdf/test_pdf_base.py``), so these tests
assert the parts, not a pre-slugified form.
"""

import pytest

from evan.models import Fee, Registration
from evan.services.pdf.response import PdfResponse
from evan.site.views.file_makers.registrations import (
    CertificatePdfMaker,
    InvitationLetterPdfMaker,
    InvoicePdfMaker,
    ReceiptPdfMaker,
)
from tests._factories import EventFactory, UserFactory


@pytest.mark.django_db
class TestDefaultFilename:
    """Each maker builds a filename carrying the event code, doc slug, name and uuid."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.event = EventFactory()
        Fee.objects.create(event=self.event, type="regular", value=100)
        self.user = UserFactory(first_name="Jane", last_name="Doe")
        self.registration = Registration.objects.create(
            event=self.event, user=self.user, fee_type="regular", is_accepted=True
        )

    def _filename(self, maker_cls):
        return maker_cls.default_filename(self.registration)

    def test_receipt_filename_contains_all_parts(self):
        """Receipt filename carries event code, slug, name and uuid."""
        filename = self._filename(ReceiptPdfMaker)

        assert filename == f"{self.event.code}-receipt-{self.user.name}-{self.registration.uuid}.pdf"
        assert self.event.code in filename
        assert "receipt" in filename
        assert self.user.name in filename
        assert str(self.registration.uuid) in filename

    def test_invoice_filename_uses_invoice_slug(self):
        """Invoice filename uses the invoice doc slug."""
        assert (
            self._filename(InvoicePdfMaker)
            == f"{self.event.code}-invoice-{self.user.name}-{self.registration.uuid}.pdf"
        )

    def test_invitation_letter_filename_uses_invitation_letter_slug(self):
        """Invitation letter filename uses the invitation-letter doc slug."""
        assert (
            self._filename(InvitationLetterPdfMaker)
            == f"{self.event.code}-invitation-letter-{self.user.name}-{self.registration.uuid}.pdf"
        )

    def test_certificate_filename_uses_certificate_slug(self):
        """Certificate filename uses the certificate doc slug."""
        assert (
            self._filename(CertificatePdfMaker)
            == f"{self.event.code}-certificate-{self.user.name}-{self.registration.uuid}.pdf"
        )

    def test_pdf_response_slugifies_default_filename(self):
        """The raw default filename is slugified once by PdfResponse."""
        raw = CertificatePdfMaker.default_filename(self.registration)
        sanitized = PdfResponse(filename=raw).filename

        assert sanitized == f"{self.event.code}-certificate-jane-doe-{self.registration.uuid}.pdf"
        assert " " not in sanitized
        assert sanitized.endswith(".pdf")

    def test_name_with_accents_is_slugified_by_pdf_response(self):
        """Accents in the raw name survive default_filename and are ASCII-safe after PdfResponse."""
        self.user.first_name = "José"
        self.user.last_name = "García"
        self.user.save()

        raw = CertificatePdfMaker.default_filename(self.registration)
        sanitized = PdfResponse(filename=raw).filename

        assert "José" in raw
        assert "jose-garcia" in sanitized
        assert sanitized.endswith(".pdf")
