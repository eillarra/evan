import json

from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import SAFE_METHODS, BasePermission

from ...serializers.rel.files import FileSerializer
from .base import RelModelViewSet


class FilePermission(BasePermission):
    """Permissions for related files."""

    def has_permission(self, request, view):
        """Check if the user has permission to access the view."""
        if not bool(request.user and request.user.is_authenticated):
            return False

        rel_object = view.get_content_object()

        if hasattr(rel_object, "event") and rel_object.event:
            return rel_object.event.can_be_managed_by(request.user)
        elif hasattr(rel_object, "can_be_managed_by"):
            return rel_object.can_be_managed_by(request.user)

        return False

    def has_object_permission(self, request, view, obj):
        """Check if the user has permission to manipulate the Timesheet object."""
        if request.method in SAFE_METHODS:
            return True

        return obj.content_object.files_can_be_managed_by(request.user)


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
        request.data["type"] = json_data.get("type", "private")
        request.data["description"] = json_data.get("description", "")
        request.data["tags"] = json.dumps(json_data.get("tags", []))
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Perform create action for related files."""
        serializer.save(content_object=self.get_content_object())
