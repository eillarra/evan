"""Tests for invoice PDF generation."""

import pytest
from django.template import engines

from evan.models import Fee, Registration
from tests._factories import EventFactory, UserFactory


@pytest.mark.django_db
class TestInvoiceTemplateInvoiceAddress:
    """Test invoice address rendering in invoice template."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Create a paid registration."""
        self.event = EventFactory()
        Fee.objects.create(event=self.event, type="regular", value=100)
        self.user = UserFactory(first_name="John", last_name="Doe")
        self.registration = Registration.objects.create(
            event=self.event, user=self.user, fee_type="regular", is_accepted=True, paid=100
        )

    def _render_invoice(self):
        """Render the invoice template with current registration."""
        engine = engines["django"]
        template = engine.get_template("pdf/documents/invoice.html")
        context = {
            "registration": self.registration,
            "signature_html": "",
            "current_date": "",
            "logo_path": "",
            "date_format": "",
        }
        return template.render(context)

    def test_invoice_address_rendered_when_set(self):
        """Invoice address block appears under the user name when configured."""
        invoice_address = (
            "Universidade do Porto, FEUP\nRua Dr. Roberto Frias, s/n\n4200-465 Porto\nPortugal\nNIF: 501413197"
        )
        self.registration.invoice_address = invoice_address
        self.registration.save()

        html = self._render_invoice()

        assert "Invoice" in html
        assert "Universidade do Porto, FEUP" in html
        assert "NIF: 501413197" in html
        assert "<br>" in html or "<br />" in html

    def test_invoice_address_omitted_when_blank(self):
        """No extra address block is printed when invoice_address is empty."""
        html = self._render_invoice()

        assert "Invoice" in html
        assert "Universidade do Porto, FEUP" not in html
