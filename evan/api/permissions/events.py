from rest_framework.exceptions import NotFound
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, IsAuthenticatedOrReadOnly

from evan.models import Event


class EventPermission(IsAuthenticatedOrReadOnly):
    """
    LIST and CREATE are not possible at API level.
    """

    def has_object_permission(self, request, view, obj):
        """
        Anybody can RETRIEVE the public event information, and DELETE is not possible at API level.
        Only event organizers (and Staff) can UPDATE a event.
        """
        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return False
        return obj.editable_by_user(request.user)


class EventRelatedPermission(IsAuthenticated):
    """TODO: see if both classes can be combined."""

    def has_permission(self, request, view):
        try:
            event = Event.objects.get(code=view.kwargs.get("code"))
        except Event.DoesNotExist as exc:
            raise NotFound("Event does not exist.") from exc
        return event.editable_by_user(request.user)

    def has_object_permission(self, request, view, obj):
        return False


class EventRelatedViewOnlyPermission:
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class EventRelatedObjectPermission(IsAuthenticated):
    allow_delete = True

    def get_event_id(self, obj):
        return obj.event_id

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE" and not self.allow_delete:
            return False

        event = Event.objects.get(id=self.get_event_id(obj))
        return event.editable_by_user(request.user)


class EventAttendeePermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Users can only RETRIEVE attendees' list if they are also regfistered.
        """
        return obj.registrations.filter(user_id=request.user.id).exists()
