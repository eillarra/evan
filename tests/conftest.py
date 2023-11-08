import arrow
import pytest
from rest_framework.test import APIClient

from evan.models.rel.permissions import Permission
from evan.utils.factories import (
    EventFactory,
    UserFactory,
)


@pytest.fixture()
def api_client():
    """A Django REST framework test client instance."""
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture()
def now():
    """An Arrow UTC instance."""
    return arrow.utcnow()


@pytest.fixture
def test_event(db):
    event = EventFactory()
    return event


@pytest.fixture
def test_event_manager(db, test_event):
    user = UserFactory()
    test_event.acl.create(user=user, level=Permission.ADMIN)
    return user
