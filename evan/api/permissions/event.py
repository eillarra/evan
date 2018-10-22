from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly, IsAuthenticated

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
        if request.method == 'DELETE':
            return False
        return obj.editable_by_user(request.user)


class EventRelatedPermission(IsAuthenticated):
    """TODO: see if both classes can be combined."""
    def has_permission(self, request, view):
        event = Event.objects.get(code=view.kwargs.get('code'))
        return event.editable_by_user(request.user)

    def has_object_permission(self, request, view, obj):
        return False


class EventRelatedObjectPermission(IsAuthenticated):

    def get_event_id(self, obj):
        return obj.event_id

    def has_object_permission(self, request, view, obj):
        event = Event.objects.get(id=self.get_event_id(obj))
        return event.editable_by_user(request.user)
