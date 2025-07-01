"""Tests for admin mixins."""

import pytest
from django.contrib.admin import ModelAdmin, site
from django.contrib.admin.actions import delete_selected
from django.test import RequestFactory

from evan.admin.mixins import HideDeleteActionMixin
from evan.models import Event
from tests._factories import UserFactory


class _TestModelAdmin(HideDeleteActionMixin, ModelAdmin):
    """Test model admin that uses the HideDeleteActionMixin."""

    def some_action(self, request, queryset):
        """Test action that should be preserved."""
        pass

    some_action.short_description = "Some test action"

    # Explicitly include delete_selected to test the mixin functionality
    actions = [delete_selected, "some_action"]


@pytest.mark.django_db
class TestHideDeleteActionMixin:
    """Test the HideDeleteActionMixin."""

    def test_superuser_cannot_delete(self):
        """Test that delete action is hidden for superusers."""
        admin = _TestModelAdmin(Event, site)
        request = RequestFactory().get("/")
        request.user = UserFactory(is_superuser=True)

        actions = admin.get_actions(request)
        # The mixin should remove delete_selected for superusers
        assert "delete_selected" not in actions
        # But other actions should still be there
        assert "some_action" in actions

    def test_mixin_preserves_other_actions(self):
        """Test that the mixin preserves other admin actions."""
        admin = _TestModelAdmin(Event, site)
        request = RequestFactory().get("/")
        request.user = UserFactory()

        actions = admin.get_actions(request)
        # Should have our custom action
        assert "some_action" in actions
        # Should have the total actions we expect
        assert len(actions) >= 1
