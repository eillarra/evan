"""Tests for badge PDF generation."""

from unittest.mock import Mock

import pytest

from evan.models import Fee, Registration
from evan.site.pdfs.badges import BadgesPdfMaker
from evan.utils.factories import UserFactory


@pytest.mark.django_db
class TestBadgesPdfMaker:
    """Test the BadgesPdfMaker class."""

    def test_badges_pdf_with_custom_colors(self, t_event) -> None:
        """Test that badge PDF uses custom colors from event configuration."""
        # Set up badge configuration on event
        t_event.extra_data = {
            "badges": {
                "default": "#2196F3",
                "guest": "#4CAF50",
                "fee_colors": {"student": "#2ecc71", "regular": "#f39c12"},
            }
        }
        t_event.save()

        # Create fees
        Fee.objects.create(event=t_event, type="student", value=50)
        Fee.objects.create(event=t_event, type="regular", value=100)

        # Create users and registrations with different fee types
        user1 = UserFactory()
        user2 = UserFactory()

        reg1 = Registration.objects.create(event=t_event, user=user1, fee_type="student", is_accepted=True)
        reg2 = Registration.objects.create(event=t_event, user=user2, fee_type="regular", is_accepted=True)

        registrations = Registration.objects.filter(id__in=[reg1.id, reg2.id])

        with pytest.MonkeyPatch().context() as m:
            mock_wrapdf = Mock()
            mock_wrapdf.__enter__ = Mock(return_value=mock_wrapdf)
            mock_wrapdf.__exit__ = Mock(return_value=None)
            mock_wrapdf.parts = []
            mock_wrapdf.get.return_value = b"fake pdf content"

            m.setattr("evan.site.pdfs.badges.Wrapdf", Mock(return_value=mock_wrapdf))

            BadgesPdfMaker(registrations=registrations, filename="test.pdf")

            # Verify that badges were generated (parts added to PDF)
            assert len(mock_wrapdf.parts) >= 2  # At least one badge per registration

    def test_badges_pdf_with_accompanying_persons(self, t_event) -> None:
        """Test that badge PDF generates badges for accompanying persons with main registrant's name."""
        # Set up badge configuration on event
        t_event.extra_data = {"badges": {"default": "#2196F3", "guest": "#4CAF50", "fee_colors": {}}}
        t_event.save()

        # Create fee
        Fee.objects.create(event=t_event, type="regular", value=100)

        # Create registration with accompanying persons
        user = UserFactory()
        registration = Registration.objects.create(
            event=t_event,
            user=user,
            fee_type="regular",
            is_accepted=True,
            extra_data={
                "accompanying_persons": [
                    {"name": "John Doe", "dietary": "none", "selected_social_events": []},
                    {"name": "Jane Smith", "dietary": "vegetarian", "selected_social_events": []},
                ]
            },
        )

        registrations = Registration.objects.filter(id=registration.id)

        with pytest.MonkeyPatch().context() as m:
            mock_wrapdf = Mock()
            mock_wrapdf.__enter__ = Mock(return_value=mock_wrapdf)
            mock_wrapdf.__exit__ = Mock(return_value=None)
            mock_wrapdf.parts = []
            mock_wrapdf.get.return_value = b"fake pdf content"

            m.setattr("evan.site.pdfs.badges.Wrapdf", Mock(return_value=mock_wrapdf))

            BadgesPdfMaker(registrations=registrations, filename="test.pdf")

            # Should have 3 badges: 1 for registrant + 2 for accompanying persons
            assert len(mock_wrapdf.parts) == 3

    def test_badges_pdf_fallback_to_default_color(self, t_event) -> None:
        """Test that badge PDF falls back to default color for unknown fee types."""
        # Set up badge configuration on event
        t_event.extra_data = {"badges": {"default": "#2196F3", "guest": "#4CAF50", "fee_colors": {}}}
        t_event.save()

        # Create a fee type and registration, but ensure the fee type is not in badge config
        Fee.objects.create(event=t_event, type="special", value=75)

        user = UserFactory()
        registration = Registration.objects.create(event=t_event, user=user, fee_type="special", is_accepted=True)

        registrations = Registration.objects.filter(id=registration.id)

        with pytest.MonkeyPatch().context() as m:
            mock_wrapdf = Mock()
            mock_wrapdf.__enter__ = Mock(return_value=mock_wrapdf)
            mock_wrapdf.__exit__ = Mock(return_value=None)
            mock_wrapdf.parts = []
            mock_wrapdf.get.return_value = b"fake pdf content"

            m.setattr("evan.site.pdfs.badges.Wrapdf", Mock(return_value=mock_wrapdf))

            BadgesPdfMaker(registrations=registrations, filename="test.pdf")

            # Should still generate badge with default color (since "special" not in fee_colors)
            assert len(mock_wrapdf.parts) == 1
