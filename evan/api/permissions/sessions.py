from rest_framework.permissions import IsAuthenticated


class SessionPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Session organizers can UPDATE the object.
        Event administrators can UPDATE the object, and DELETE it if the event is not closed.
        """
        event = obj.event
        if request.method == "DELETE":
            return event.editable_by_user(request.user) and not event.is_closed
        return obj.editable_by_user(request.user) or event.editable_by_user(request.user)
