from datetime import UTC, datetime, time, timedelta

import arrow
import pytest
from rest_framework.test import APIClient

from evan.models.rel.permissions import Permission
from tests._factories import (
    EventFactory,
    UserFactory,
)


def _fresh_event(event):
    """Reload an event so date fields match their stored representations.

    :param event: The event fixture instance.
    :returns: The refreshed event.
    """
    event.refresh_from_db()
    return event


@pytest.fixture()
def open_registration_window(t_event, monkeypatch):
    """Freeze time just after the event's registration opens.

    :param t_event: The standard test event.
    :param monkeypatch: Pytest monkeypatch used for the clock.
    """
    event = _fresh_event(t_event)
    fixed = datetime.combine(event.registration_start_date, time.min, tzinfo=UTC) + timedelta(hours=1)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fixed)
    assert event.is_open_for_registration


@pytest.fixture()
def not_yet_open_registration_window(t_event, monkeypatch):
    """Freeze time just before the event's registration opens.

    :param t_event: The standard test event.
    :param monkeypatch: Pytest monkeypatch used for the clock.
    """
    event = _fresh_event(t_event)
    fixed = datetime.combine(event.registration_start_date, time.min, tzinfo=UTC) - timedelta(hours=1)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fixed)
    assert not event.is_open_for_registration


@pytest.fixture()
def onsite_registration_window(t_event, monkeypatch):
    """Open an on-site window and freeze time inside it.

    :param t_event: The standard test event.
    :param monkeypatch: Pytest monkeypatch used for the clock.
    """
    event = _fresh_event(t_event)
    event.registration_onsite_deadline = event.registration_deadline + timedelta(days=2)
    event.save(update_fields=["registration_onsite_deadline"])
    fixed = event.registration_deadline + timedelta(hours=1)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fixed)
    assert event.is_open_for_registration


@pytest.fixture()
def closed_registration_window(t_event, monkeypatch):
    """Freeze time after the event's registration window has closed.

    :param t_event: The standard test event.
    :param monkeypatch: Pytest monkeypatch used for the clock.
    """
    event = _fresh_event(t_event)
    end = event.registration_onsite_deadline or event.registration_deadline
    fixed = end + timedelta(days=1)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fixed)
    assert not event.is_open_for_registration


@pytest.fixture()
def api_client():
    """A Django REST framework test client instance."""
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture()
def now():
    """An Arrow UTC instance."""
    return arrow.utcnow()


@pytest.fixture
def t_event(db):
    from evan.models import Event, Fee

    event = EventFactory(listing_status=Event.ListingStatus.LISTED)
    Fee.objects.create(event=event, type="regular", value=100)

    return event


@pytest.fixture
def t_event_manager(db, t_event):
    user = UserFactory()
    t_event.acl.create(user=user, level=Permission.ADMIN)
    return user


@pytest.fixture
def t_superuser(db):
    """Create a superuser for admin testing."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_superuser("admin", "admin@test.com", "password")
