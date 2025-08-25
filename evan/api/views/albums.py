from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Album

from ..permissions import EventAttendeePermission, EventRelatedObjectPermission
from ..serializers.albums import AlbumListSerializer, AlbumSerializer
from ..viewsets import EventRelatedViewSet


class AlbumsPermission(EventAttendeePermission):
    """Permission for albums - only registered attendees (not no-show) and event managers."""

    def has_permission(self, request, view):
        """Check if user has permission to access albums list."""
        if request.method in ["OPTIONS", "HEAD"]:
            return True

        # First check if the user has basic permissions
        if not super().has_permission(request, view):
            return False

        # Get the event from the view
        event = view.get_event()

        # Event managers can do everything
        if event.can_be_managed_by(request.user):
            return True

        # For GET requests, check if user is a registered attendee (not no-show)
        if request.method == "GET":
            return event.registrations.filter(user_id=request.user.id, is_accepted=True, no_show=False).exists()

        # For other methods (POST for creating albums), only event managers
        return False

    def has_object_permission(self, request, view, obj):
        """Check if user is a registered attendee (not no-show) or event manager."""
        if request.method in ["OPTIONS", "HEAD"]:
            return True

        # Use the album's access control method
        return obj.is_accessible_by_user(request.user)


class AlbumPermission(EventRelatedObjectPermission):
    """Permission for individual album operations."""

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific album."""
        if request.method in ["OPTIONS", "HEAD"]:
            return True

        # Use the album's access control method
        return obj.is_accessible_by_user(request.user)


class AlbumsViewSet(EventRelatedViewSet):
    """API endpoint for listing and creating albums for an event."""

    permission_classes = [AlbumsPermission]
    queryset = Album.objects.prefetch_related("files")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        # For photo gallery, we need full album data with photos
        # Check if request includes a parameter to get full data
        if self.action == "list" and self.request.GET.get("include_photos") != "true":
            return AlbumListSerializer
        return AlbumSerializer


class AlbumViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    """API endpoint for individual album operations."""

    permission_classes = [AlbumPermission]
    queryset = Album.objects.prefetch_related("files")
    serializer_class = AlbumSerializer
