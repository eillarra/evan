from rest_framework.exceptions import NotFound
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly

from evan.models import Event


class EventPermission(IsAuthenticatedOrReadOnly):
    """Permission class for Event model.

    Anybody can RETRIEVE the public event information, and DELETE is not possible at API level.
    Only event organizers (and Staff) can UPDATE an event."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return False
        return obj.editable_by_user(request.user)


class EventRelatedPermission(BasePermission):
    _event = None

    allow_list_to_all = False
    allow_retrieve_to_all = False
    allow_create_to_manager = True
    allow_update_to_manager = False
    allow_delete_to_manager = False

    def get_event(self, view) -> Event:
        if not self._event:
            try:
                self._event = Event.objects.get(code=view.kwargs.get("code"))
            except Event.DoesNotExist as exc:
                raise NotFound("Event does not exist.") from exc
        return self._event

    def has_permission(self, request, view):
        if request.method in ["OPTIONS", "HEAD"]:
            return True

        event = self.get_event(view)

        if request.method == "GET":
            if "pk" in view.kwargs:
                return self.allow_retrieve_to_all or event.editable_by_user(request.user)
            return self.allow_list_to_all or event.editable_by_user(request.user)

        if request.method == "POST":
            return self.allow_create_to_manager and event.editable_by_user(request.user)

        if request.method in ["PUT", "PATCH"]:
            return self.allow_update_to_manager and event.editable_by_user(request.user)

        if request.method == "DELETE":
            return self.allow_delete_to_manager and event.editable_by_user(request.user)

        return False


class EventRelatedObjectPermission(BasePermission):
    _event = None

    allow_retrieve_to_all = False
    allow_update_to_manager = True
    allow_delete_to_manager = False

    def get_event_id(self, obj):
        """Get the event ID from the object. Can be overridden by subclasses."""
        return obj.event_id

    def get_event(self, obj) -> Event:
        if not self._event:
            try:
                event_id = self.get_event_id(obj)
                self._event = Event.objects.get(id=event_id)
            except Event.DoesNotExist as exc:
                raise NotFound("Event does not exist.") from exc
        return self._event

    def has_object_permission(self, request, view, obj):
        if request.method in ["OPTIONS", "HEAD"]:
            return True

        event = self.get_event(obj)

        if request.method == "GET":
            return self.allow_retrieve_to_all or event.editable_by_user(request.user)

        if request.method in ["PUT", "PATCH"]:
            return self.allow_update_to_manager and event.editable_by_user(request.user)

        if request.method == "DELETE":
            return self.allow_delete_to_manager and event.editable_by_user(request.user)

        return False


class EventAttendeePermission(IsAuthenticated):
    """Permission class for attendees and event managers to access event-specific features."""

    # Permission flags
    allow_retrieve_to_all = False

    def has_permission(self, request, view):
        """Check if user is authenticated (delegated to parent class)."""
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        """Check if user is an attendee or event manager for the specific event."""
        if request.method in ["OPTIONS", "HEAD"]:
            return True

        # For GET requests (like attendees list)
        if request.method == "GET":
            if self.allow_retrieve_to_all:
                return True
            # Allow if user is an attendee
            if obj.registrations.filter(user_id=request.user.id).exists():
                return True
            # Also allow if user is an event manager
            return obj.editable_by_user(request.user)

        # For POST requests (like contact), check if user is an attendee OR an event manager
        if request.method == "POST":
            # Allow if user is an attendee
            if obj.registrations.filter(user_id=request.user.id).exists():
                return True
            # Also allow if user is an event manager
            return obj.editable_by_user(request.user)

        return False
