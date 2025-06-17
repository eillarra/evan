"""Utility functions for API views."""


def user_is_manager_of_event(user, event):
    """Check if a user can manage an event."""
    return bool(user and user.is_authenticated) and event.can_be_managed_by(user)
