"""Tests for the public event listing on the home page."""

import json

import pytest
from django.urls import reverse

from tests._factories import EventFactory


@pytest.mark.site
@pytest.mark.django_db
class TestHomeEventListing:
    """Only listed, upcoming events appear in the home page listing."""

    def _listing_codes(self, client) -> set[str]:
        response = client.get(reverse("homepage"), HTTP_X_INERTIA="true")
        props = json.loads(response.content)["props"]
        return {event["code"] for event in props["events"]}

    def test_listed_upcoming_events_appear(self, client):
        EventFactory(code="listed-event", listing_status="listed")

        assert "listed-event" in self._listing_codes(client)

    def test_pending_events_never_appear(self, client):
        EventFactory(code="pending-event", listing_status="pending_review")

        assert "pending-event" not in self._listing_codes(client)

    def test_declined_events_never_appear(self, client):
        EventFactory(code="declined-event", listing_status="declined")

        assert "declined-event" not in self._listing_codes(client)

    def test_past_events_never_appear(self, client):
        from datetime import timedelta

        from django.utils import timezone

        past = EventFactory(code="past-event", listing_status="listed")
        past.end_date = timezone.now().date() - timedelta(days=1)
        past.save()

        assert "past-event" not in self._listing_codes(client)
