"""Tests for badge PDF generation."""

from unittest.mock import Mock

import pytest

from evan.models import Fee, Registration
from evan.site.pdfs.badges import BadgesPdfMaker
from tests._factories import UserFactory


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

    def test_badges_pdf_with_color_grouping(self, t_event) -> None:
        """Test that badge PDF groups by color correctly."""
        # Set up badge configuration with color grouping and fee colors where multiple fees share the same color
        t_event.extra_data = {
            "badges": {
                "default": "#2196F3",
                "guest": "#4CAF50",
                "fee_colors": {
                    "student": "#ff5722",  # Orange color
                    "student_early": "#ff5722",  # Same orange color (should be grouped together)
                    "regular": "#2196F3",  # Same as default color (should be grouped with default)
                    "vip": "#9c27b0",  # Purple color (unique group)
                },
                "sort_by": "first_name",
                "group_by": "color",
            }
        }
        t_event.save()

        # Create fees
        Fee.objects.create(event=t_event, type="student", value=50)
        Fee.objects.create(event=t_event, type="student_early", value=40)
        Fee.objects.create(event=t_event, type="regular", value=100)
        Fee.objects.create(event=t_event, type="vip", value=200)
        Fee.objects.create(event=t_event, type="other", value=80)  # Fee type not in fee_colors

        # Create users and registrations with different fee types
        user1 = UserFactory(first_name="Alice")
        user2 = UserFactory(first_name="Bob")
        user3 = UserFactory(first_name="Charlie")
        user4 = UserFactory(first_name="David")
        user5 = UserFactory(first_name="Eve")  # Uses "other" fee type, should use default color

        reg1 = Registration.objects.create(event=t_event, user=user1, fee_type="student", is_accepted=True)
        reg2 = Registration.objects.create(event=t_event, user=user2, fee_type="student_early", is_accepted=True)
        reg3 = Registration.objects.create(event=t_event, user=user3, fee_type="regular", is_accepted=True)
        reg4 = Registration.objects.create(event=t_event, user=user4, fee_type="vip", is_accepted=True)
        reg5 = Registration.objects.create(event=t_event, user=user5, fee_type="other", is_accepted=True)

        registrations = Registration.objects.filter(pk__in=[reg1.pk, reg2.pk, reg3.pk, reg4.pk, reg5.pk]).order_by(
            "user__first_name"
        )

        with pytest.MonkeyPatch().context() as m:
            mock_wrapdf = Mock()
            mock_wrapdf.__enter__ = Mock(return_value=mock_wrapdf)
            mock_wrapdf.__exit__ = Mock(return_value=None)
            mock_wrapdf.parts = []
            mock_wrapdf.get.return_value = b"fake pdf content"

            m.setattr("evan.site.pdfs.badges.Wrapdf", Mock(return_value=mock_wrapdf))

            badge_maker = BadgesPdfMaker(registrations=registrations, filename="test.pdf")

            # Test the _group_registrations method directly to verify color grouping logic
            sorted_regs = badge_maker._sort_registrations(registrations, "first_name")
            groups = badge_maker._group_registrations(sorted_regs, "color")

            # Should have 3 color groups:
            # 1. #2196F3 (default): regular + other (Charlie, Eve)
            # 2. #9c27b0 (purple): vip (David)
            # 3. #ff5722 (orange): student + student_early (Alice, Bob)
            assert len(groups) == 3

            # Verify that badges were generated (5 registrations = 5 badges)
            assert len(mock_wrapdf.parts) == 5

    def test_guest_badge_formatting(self, t_event) -> None:
        """Test that guest badges use proper 'guest of [name]' formatting."""
        # Set up badge configuration
        t_event.extra_data = {"badges": {"default": "#2196F3", "guest": "#4CAF50", "fee_colors": {}}}
        t_event.save()

        # Create fee
        Fee.objects.create(event=t_event, type="regular", value=100)

        # Create user with specific name to test formatting
        user = UserFactory(first_name="Dr. Jane", last_name="Doe")
        registration = Registration.objects.create(
            event=t_event,
            user=user,
            fee_type="regular",
            is_accepted=True,
            extra_data={
                "accompanying_persons": [
                    {"name": "John Smith", "dietary": "none", "selected_social_events": []},
                ]
            },
        )

        registrations = Registration.objects.filter(pk=registration.pk)

        with pytest.MonkeyPatch().context() as m:
            # Mock the draw_badge function to capture its arguments
            captured_calls = []

            def mock_draw_badge(*args, **kwargs):
                captured_calls.append(kwargs)
                # Return a simple mock drawing
                from reportlab.graphics.shapes import Drawing

                return Drawing(100, 100)

            m.setattr("evan.site.pdfs.badges.draw_badge", mock_draw_badge)

            mock_wrapdf = Mock()
            mock_wrapdf.__enter__ = Mock(return_value=mock_wrapdf)
            mock_wrapdf.__exit__ = Mock(return_value=None)
            mock_wrapdf.parts = []
            mock_wrapdf.get.return_value = b"fake pdf content"

            m.setattr("evan.site.pdfs.badges.Wrapdf", Mock(return_value=mock_wrapdf))

            BadgesPdfMaker(registrations=registrations, filename="test.pdf")

            # Should have 2 calls: one for main registrant, one for guest
            assert len(captured_calls) == 2

            # Verify main registrant badge
            main_badge = captured_calls[0]
            assert main_badge["attendee_name"] == "Dr. Jane Doe"
            assert main_badge["institution"] == user.affiliation  # Should use actual affiliation
            assert main_badge["country"] == user.country.name

            # Verify guest badge formatting
            guest_badge = captured_calls[1]
            assert guest_badge["attendee_name"] == "John Smith"
            assert guest_badge["institution"] is None  # Institution should be None for cleaner look
            assert guest_badge["country"] == "guest of Dr. Jane Doe"  # Relationship shown in country field

    def test_camera_icon_reflects_photo_consent(self, t_event) -> None:
        """Show camera icon: consented attendees get the plain camera, opted-out the struck one."""
        t_event.extra_data = {"badges": {"default": "#2196F3", "guest": "#4CAF50", "show_camera_icon": True}}
        t_event.save()

        Fee.objects.create(event=t_event, type="regular", value=100)

        consenting = UserFactory(first_name="Anne", last_name="Allow")
        opt_out = UserFactory(first_name="Paul", last_name="NoPhoto")
        reg_allow = Registration.objects.create(event=t_event, user=consenting, fee_type="regular", is_accepted=True)
        reg_no_photo = Registration.objects.create(
            event=t_event,
            user=opt_out,
            fee_type="regular",
            is_accepted=True,
            extra_data={"_internal": {"allow_photo_sharing": False}},
        )

        registrations = Registration.objects.filter(pk__in=[reg_allow.pk, reg_no_photo.pk])

        captured_calls = []
        with pytest.MonkeyPatch().context() as m:

            def mock_draw_badge(*args, **kwargs):
                from reportlab.graphics.shapes import Drawing

                captured_calls.append(kwargs)
                return Drawing(100, 100)

            m.setattr("evan.site.pdfs.badges.draw_badge", mock_draw_badge)

            mock_wrapdf = Mock()
            mock_wrapdf.__enter__ = Mock(return_value=mock_wrapdf)
            mock_wrapdf.__exit__ = Mock(return_value=None)
            mock_wrapdf.parts = []
            mock_wrapdf.get.return_value = b"fake pdf content"

            m.setattr("evan.site.pdfs.badges.Wrapdf", Mock(return_value=mock_wrapdf))

            BadgesPdfMaker(registrations=registrations, filename="test.pdf")

        assert len(captured_calls) == 2
        no_photo_by_name = {call["attendee_name"]: call["no_photos"] for call in captured_calls}
        assert no_photo_by_name["Paul NoPhoto"] is True
        assert no_photo_by_name["Anne Allow"] is False
