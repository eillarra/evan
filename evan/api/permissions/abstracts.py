from rest_framework.permissions import IsAuthenticated


class AbstractPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Users can only RETRIEVE or UPDATE their abstract.
        DELETE is not allowed at API level.
        """
        if request.method == "DELETE":
            return False
        return obj.user_id == request.user.id
