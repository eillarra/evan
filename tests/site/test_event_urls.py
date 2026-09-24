"""Tests for the event URL layout: public page at /e/<code>/, console at /e/<code>/manage/."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_public_page_reverse():
    """The event:app name resolves to the public page."""
    assert reverse("event:app", args=["evt"]) == "/e/evt/"


@pytest.mark.django_db
def test_manage_reverses():
    """Console routes live under /e/<code>/manage/."""
    assert reverse("event:manage", args=["evt"]) == "/e/evt/manage/"
    assert reverse("event:badges", args=["evt"]) == "/e/evt/manage/badges.pdf"
    assert reverse("event:event_excel", args=["evt", "registrations"]) == "/e/evt/manage/registrations.xlsx"
    assert reverse("event:registration_preview", args=["evt"]) == "/e/evt/manage/registration-preview/"
