"""Tests for venue management functionality."""

import pytest

from tests._factories import EventFactory, VenueFactory


@pytest.mark.django_db
class TestVenueMainConstraint:
    """Test the main venue constraint logic."""

    def test_single_main_venue_per_event(self):
        """Test that only one venue can be main per event."""
        event = EventFactory()

        # Create first venue as main
        venue1 = VenueFactory(event=event, name="Main Conference Center", is_main=True)
        assert venue1.is_main is True

        # Create second venue as main - should make first venue non-main
        venue2 = VenueFactory(event=event, name="Secondary Building", is_main=True)

        # Refresh venue1 from database
        venue1.refresh_from_db()

        # Check that only venue2 is main now
        assert venue1.is_main is False
        assert venue2.is_main is True

    def test_update_venue_to_main_removes_previous_main(self):
        """Test that updating a venue to main removes previous main status."""
        event = EventFactory()

        # Create two venues, first one is main
        venue1 = VenueFactory(event=event, name="Original Main", is_main=True)
        venue2 = VenueFactory(event=event, name="Secondary", is_main=False)

        # Update second venue to be main
        venue2.is_main = True
        venue2.save()

        # Refresh venue1 from database
        venue1.refresh_from_db()

        # Check that only venue2 is main now
        assert venue1.is_main is False
        assert venue2.is_main is True

    def test_multiple_non_main_venues_allowed(self):
        """Test that multiple venues can exist with is_main=False."""
        event = EventFactory()

        venue1 = VenueFactory(event=event, name="Building A", is_main=False)
        venue2 = VenueFactory(event=event, name="Building B", is_main=False)
        venue3 = VenueFactory(event=event, name="Building C", is_main=False)

        assert venue1.is_main is False
        assert venue2.is_main is False
        assert venue3.is_main is False

    def test_main_venue_constraint_per_event(self):
        """Test that main venue constraint is per event, not global."""
        event1 = EventFactory()
        event2 = EventFactory()

        # Create main venues for both events
        venue1 = VenueFactory(event=event1, name="Event 1 Main", is_main=True)
        venue2 = VenueFactory(event=event2, name="Event 2 Main", is_main=True)

        # Both should remain main since they're for different events
        assert venue1.is_main is True
        assert venue2.is_main is True
