from rest_framework.permissions import IsAuthenticated


class UserPermission(IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        """
        Users can only RETRIEVE or UPDATE their own information.
        DELETE is not allowed at API level.
        """
        if request.method == 'DELETE':
            return False
        return obj.id == request.user.id
