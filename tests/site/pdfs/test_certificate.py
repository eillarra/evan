"""Tests certificate of attendance PDF template rendering."""

import pytest
from django.template import engines

from evan.models import Fee, Registration
from tests._factories import EventFactory, UserFactory


@pytest.mark.django_db
class TestCertificateTemplate:
    """Test certificate rendering in the certificate template."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.event = EventFactory(
            name="Evan 2026",
            full_name="Evan Conference 2026",
            city="Ghent",
            country="BE",
            website="https://evan.example",
            signature="Kind regards",
        )
        Fee.objects.create(event=self.event, type="regular", value=100)
        self.user = UserFactory(first_name="Jane", last_name="Doe", affiliation="UGent")
        self.registration = Registration.objects.create(
            event=self.event, user=self.user, fee_type="regular", is_accepted=True
        )

    def _render_certificate(self) -> str:
        """Render the certificate template for the current registration."""
        engine = engines["django"]
        template = engine.get_template("pdf/documents/certificate.html")
        context = {
            "registration": self.registration,
            "event": self.event,
            "signature_html": "<p>Kind regards</p>",
            "current_date": "",
            "logo_path": "",
            "date_format": "",
        }
        return template.render(context)

    def test_certificate_includes_attendee_and_affiliation(self):
        """Attendee name and affiliation appear on the certificate."""
        html = self._render_certificate()

        assert "Jane Doe" in html
        assert "UGent" in html

    def test_certificate_includes_event_location(self):
        """Event name and city appear on the certificate."""
        html = self._render_certificate()

        assert "Evan 2026" in html
        assert "Ghent" in html
        assert "Belgium" in html

    def test_certificate_includes_registration_id(self):
        """The registration UUID appears on the certificate."""
        html = self._render_certificate()

        assert str(self.registration.uuid) in html

    def test_certificate_shows_virtual_when_event_is_virtual(self):
        """A virtual event renders as 'virtually' instead of a city."""
        self.event.is_virtual = True
        self.event.save()

        html = self._render_certificate()

        assert "virtually" in html
