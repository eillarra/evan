from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly, IsAuthenticated

from toucon.models import Conference


class ConferencePermission(IsAuthenticatedOrReadOnly):
    """
    LIST and CREATE are not possible at API level.
    """
    def has_object_permission(self, request, view, obj):
        """
        Anybody can RETRIEVE the public conference information, and DELETE is not possible at API level.
        Only conference organizers (and Staff) can UPDATE a conference.
        """
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'DELETE':
            return False
        return obj.editable_by_user(request.user)


class ConferenceRelatedPermission(IsAuthenticated):
    """TODO: see if both classes can be combined."""
    def has_permission(self, request, view):
        conference = Conference.objects.get(code=view.kwargs.get('code'))
        return conference.editable_by_user(request.user)

    def has_object_permission(self, request, view, obj):
        return False


class ConferenceRelatedObjectPermission(IsAuthenticated):
    def get_conference_id(self, obj):
        return obj.conference_id

    def has_object_permission(self, request, view, obj):
        conference = Conference.objects.get(id=self.get_conference_id(obj))
        return conference.editable_by_user(request.user)
