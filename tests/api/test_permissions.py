"""Tests for API permissions."""

import pytest
from django.test import RequestFactory

from evan.api.permissions import (
    EventManagerPermission,
    EventPermission,
    FilePermission,
    RegistrationPermission,
    UserPermission,
)
from evan.models import Permission
from evan.models.rel.files import File
from tests._factories import EventFactory, RegistrationFactory, UserFactory


@pytest.mark.django_db
class TestEventPermission:
    """Test EventPermission class."""

    def test_retrieve_allows_all(self):
        """Test that GET requests are allowed for everyone."""
        permission = EventPermission()
        request = RequestFactory().get("/")
        request.user = UserFactory()
        event = EventFactory()

        assert permission.has_object_permission(request, None, event) is True

    def test_delete_not_allowed(self):
        """Test that DELETE requests are not allowed."""
        permission = EventPermission()
        request = RequestFactory().delete("/")
        request.user = UserFactory()
        event = EventFactory()

        assert permission.has_object_permission(request, None, event) is False

    def test_update_allowed_for_event_manager(self):
        """Test that event managers can update events."""
        permission = EventPermission()
        request = RequestFactory().put("/")
        user = UserFactory()
        request.user = user
        event = EventFactory()

        # Create event manager permission using the Permission model directly
        Permission.objects.create(
            content_object=event,
            user=user,
            level=Permission.ADMIN,  # Use ADMIN level (5)
        )

        assert permission.has_object_permission(request, None, event) is True

    def test_update_not_allowed_for_regular_user(self):
        """Test that regular users cannot update events."""
        permission = EventPermission()
        request = RequestFactory().put("/")
        request.user = UserFactory()
        event = EventFactory()

        assert permission.has_object_permission(request, None, event) is False


@pytest.mark.django_db
class TestRegistrationPermission:
    """Test RegistrationPermission class."""

    def test_owner_can_access(self, t_event):
        """Test that registration owners can access their registrations."""
        permission = RegistrationPermission()
        user = UserFactory()
        registration = RegistrationFactory(user=user, event=t_event)

        request = RequestFactory().get("/")
        request.user = user
        assert permission.has_object_permission(request, None, registration) is True

    def test_other_user_cannot_access(self, t_event):
        """Test that other users cannot access registrations."""
        permission = RegistrationPermission()
        owner = UserFactory()
        other_user = UserFactory()
        registration = RegistrationFactory(user=owner, event=t_event)

        request = RequestFactory().get("/")
        request.user = other_user
        assert permission.has_object_permission(request, None, registration) is False

    def test_delete_not_allowed(self, t_event):
        """Test that DELETE requests are not allowed."""
        permission = RegistrationPermission()
        user = UserFactory()
        registration = RegistrationFactory(user=user, event=t_event)

        request = RequestFactory().delete("/")
        request.user = user
        assert permission.has_object_permission(request, None, registration) is False


@pytest.mark.django_db
class TestFilePermission:
    """Test FilePermission class."""

    def test_content_object_owner_can_access(self):
        """Test that users who can edit the content object can access files."""
        permission = FilePermission()
        user = UserFactory()
        event = EventFactory()

        # Create a file manually
        file = File.objects.create(content_object=event, type=File.PRIVATE, file="test/path.txt")

        # Make user an event manager
        Permission.objects.create(content_object=event, user=user, level=Permission.ADMIN)

        request = RequestFactory().delete("/")
        request.user = user
        assert permission.has_object_permission(request, None, file) is True

    def test_other_user_cannot_access(self):
        """Test that other users cannot access files."""
        permission = FilePermission()
        user = UserFactory()
        event = EventFactory()

        file = File.objects.create(content_object=event, type=File.PRIVATE, file="test/path.txt")

        request = RequestFactory().delete("/")
        request.user = user
        assert permission.has_object_permission(request, None, file) is False


@pytest.mark.django_db
class TestEventManagerPermission:
    """Test EventManagerPermission class."""

    def test_event_manager_has_permission(self):
        """Test that event managers have permission."""
        permission = EventManagerPermission()
        user = UserFactory()
        event = EventFactory()

        # Create admin-level permission
        Permission.objects.create(content_object=event, user=user, level=Permission.ADMIN)

        request = RequestFactory().get("/")
        request.user = user
        assert permission.has_permission(request, None) is True

    def test_regular_user_no_permission(self):
        """Test that regular users don't have permission."""
        permission = EventManagerPermission()
        user = UserFactory()

        request = RequestFactory().get("/")
        request.user = user
        assert permission.has_permission(request, None) is False

    def test_delete_not_allowed(self):
        """Test that DELETE requests are not allowed."""
        permission = EventManagerPermission()
        user = UserFactory()
        event = EventFactory()

        Permission.objects.create(content_object=event, user=user, level=Permission.ADMIN)

        request = RequestFactory().delete("/")
        request.user = user
        assert permission.has_permission(request, None) is False

    def test_object_permission_always_false(self):
        """Test that object permissions are always false."""
        permission = EventManagerPermission()
        user = UserFactory()

        request = RequestFactory().get("/")
        request.user = user
        assert permission.has_object_permission(request, None, user) is False


@pytest.mark.django_db
class TestUserPermission:
    """Test UserPermission class."""

    def test_user_can_access_own_info(self):
        """Test that users can access their own information."""
        permission = UserPermission()
        user = UserFactory()

        request = RequestFactory().get("/")
        request.user = user
        assert permission.has_object_permission(request, None, user) is True

    def test_other_user_cannot_access(self):
        """Test that users cannot access other users' information."""
        permission = UserPermission()
        user1 = UserFactory()
        user2 = UserFactory()

        request = RequestFactory().get("/")
        request.user = user1
        assert permission.has_object_permission(request, None, user2) is False

    def test_delete_not_allowed(self):
        """Test that DELETE requests are not allowed."""
        permission = UserPermission()
        user = UserFactory()

        request = RequestFactory().delete("/")
        request.user = user
        assert permission.has_object_permission(request, None, user) is False
