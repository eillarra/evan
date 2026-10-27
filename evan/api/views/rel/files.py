import json

from django.http import Http404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import SAFE_METHODS, BasePermission

from evan.models.rel.files import FilesMixin
from evan.services.file_guard import get_presented_secret, has_matching_secret

from ...serializers.rel.files import FileSerializer
from .base import RelModelViewSet


class FilePermission(BasePermission):
    """Permissions for related files.

    A requester may manage an object's files with that object's write
    capability, or with the object's own secret — a session's secret link
    manages that session's files and nothing else.
    """

    def has_permission(self, request, view):
        """Check if the user has permission to access the view."""
        authenticated = bool(request.user and request.user.is_authenticated)
        secret = get_presented_secret(request)

        # Refuse before resolving the object: an anonymous requester without a
        # secret must not learn whether the object exists.
        if not authenticated and not secret:
            return False

        try:
            rel_object = view.get_content_object()
        except Http404:
            if not authenticated:
                # Answer the same way as for an object that exists but is out of
                # reach, so a bad secret reveals nothing about the object either.
                return False
            raise

        if secret and has_matching_secret(rel_object, secret):
            return True

        if not authenticated or not isinstance(rel_object, FilesMixin):
            return False

        return rel_object.files_can_be_managed_by(request.user)

    def has_object_permission(self, request, view, obj):
        """Check if the user has permission to manipulate the file."""
        if request.method in SAFE_METHODS:
            return True

        rel_object = obj.content_object
        secret = get_presented_secret(request)

        if secret and has_matching_secret(rel_object, secret):
            return True

        if not isinstance(rel_object, FilesMixin):
            return False

        return rel_object.files_can_be_managed_by(request.user)


class FileViewSet(RelModelViewSet):
    """API endpoint for managing related files."""

    pagination_class = None
    parser_classes = [MultiPartParser]
    permission_classes = [FilePermission]
    serializer_class = FileSerializer

    def get_queryset(self):
        """Get queryset for related files."""
        return self.get_content_object().files  # type: ignore

    def create(self, request, *args, **kwargs):
        """Convert tags to a valid JSON object. This is necessary because we get the multipart data mengled."""
        json_data = json.loads(request.data.get("json", "{}"))
        if json_data.get("visibility"):
            request.data["visibility"] = json_data["visibility"]
        request.data["description"] = json_data.get("description", "")
        request.data["tags"] = json.dumps(json_data.get("tags", []))
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Perform create action for related files."""
        serializer.save(content_object=self.get_content_object())
