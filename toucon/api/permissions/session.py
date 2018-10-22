from rest_framework.permissions import IsAuthenticated


class SessionPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Session organizers can UPDATE the object.
        Conference administrators can UPDATE the object, and DELETE it if the conference is not closed.
        """
        conference = obj.conference
        if request.method == 'DELETE':
            return conference.editable_by_user(request.user) and not conference.is_closed
        return obj.editable_by_user(request.user) or conference.editable_by_user(request.user)
