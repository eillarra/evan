"""Tests invitation letter PDF template rendering."""

import pytest
from django.template import engines

from evan.models import Fee, InvitationLetter, Registration
from tests._factories import EventFactory, UserFactory


@pytest.mark.django_db
class TestInvitationLetterTemplate:
    """Test invitation letter rendering in the invitation_letter template."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.event = EventFactory(
            name="Evan 2026",
            full_name="Evan Conference 2026",
            city="Ghent",
            country="BE",
            website="https://evan.example",
            signature="Kind regards,\nOrganising committee",
        )
        Fee.objects.create(event=self.event, type="regular", value=100)
        self.user = UserFactory(first_name="Jane", last_name="Doe")
        self.registration = Registration.objects.create(
            event=self.event, user=self.user, fee_type="regular", is_accepted=True
        )
        self.letter = InvitationLetter.objects.create(
            registration=self.registration,
            name="Jane Doe",
            passport_number="X12345",
            nationality="Belgian",
            address="123 Main St\nGhent",
        )

    def _render_letter(self) -> str:
        """Render the invitation letter template for the current registration."""
        engine = engines["django"]
        template = engine.get_template("pdf/documents/invitation_letter.html")
        context = {
            "registration": self.registration,
            "event": self.event,
            "signature_html": "<p>Kind regards</p>",
            "current_date": "",
            "logo_path": "",
            "date_format": "",
        }
        return template.render(context)

    def test_letter_includes_recipient_details(self):
        """Recipient name, passport and nationality appear in the letter."""
        html = self._render_letter()

        assert "Jane Doe" in html
        assert "X12345" in html
        assert "Belgian" in html

    def test_letter_includes_event_details(self):
        """Event full name and city appear in the letter body."""
        html = self._render_letter()

        assert "Evan Conference 2026" in html
        assert "Ghent" in html

    def test_signature_block_includes_event_website(self):
        """Shared signature block renders the event website from the event context."""
        html = self._render_letter()

        assert "https://evan.example" in html
        assert "Sincerely yours" in html

    def test_paper_block_shown_when_submitted(self):
        """A submitted paper/poster produces a presentation paragraph."""
        self.letter.submitted = InvitationLetter.PAPER
        self.letter.submitted_title = "On Caveman PDFs"
        self.letter.save()

        html = self._render_letter()

        assert "On Caveman PDFs" in html
        assert "Paper" in html

    def test_paper_block_omitted_when_not_submitted(self):
        """No presentation paragraph when nothing was submitted."""
        html = self._render_letter()

        assert "titled" not in html
