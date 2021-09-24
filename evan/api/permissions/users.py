from rest_framework.permissions import IsAuthenticated

from evan.models import Permission


class EventManagerPermission(IsAuthenticated):
    def has_permission(self, request, view):
        """
        Event managers can read some special information, like the whole list of users at Evan.
        """
        if request.method == "DELETE":
            return False
        return Permission.objects.filter(user_id=request.user.id, level__gte=Permission.ADMIN).exists()

    def has_object_permission(self, request, view, obj):
        return False


class UserPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Users can only RETRIEVE or UPDATE their own information.
        DELETE is not allowed at API level.
        """
        if request.method == "DELETE":
            return False
        return obj.id == request.user.id
