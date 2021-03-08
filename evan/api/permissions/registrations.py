from rest_framework.permissions import IsAuthenticated


class RegistrationPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Users can only RETRIEVE, UPDATE or CHARGE (also a POST) their registrations.
        DELETE is not allowed at API level.
        """
        if request.method == "DELETE":
            return False
        return obj.user_id == request.user.id
