import json

from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import SAFE_METHODS, BasePermission

from ...serializers.rel.files import FileSerializer
from .base import RelModelViewSet


def get_presented_secret(request) -> str | None:
    """Return the secret presented by the request, if any.

    The secret travels in a header so it never lands in access logs or in the
    ``Referer`` of any outbound link.

    :param request: The incoming request.
    :returns: The presented secret, or None.
    """
    return request.headers.get("X-Evan-Secret")


class FilePermission(BasePermission):
    """Permissions for related files.

    A requester may manage an object's files with that object's write
    capability, or with the object's own secret — a session's secret link
    manages that session's files and nothing else.
    """

    def has_permission(self, request, view):
        """Check if the user has permission to access the view."""
        rel_object = view.get_content_object()
        secret = get_presented_secret(request)

        if secret and _secret_matches(rel_object, secret):
            return True

        if not bool(request.user and request.user.is_authenticated):
            return False

        if hasattr(rel_object, "event") and rel_object.event:
            return rel_object.event.can_be_managed_by(request.user)
        elif hasattr(rel_object, "can_be_managed_by"):
            return rel_object.can_be_managed_by(request.user)

        return False

    def has_object_permission(self, request, view, obj):
        """Check if the user has permission to manipulate the file."""
        if request.method in SAFE_METHODS:
            return True

        rel_object = obj.content_object
        secret = get_presented_secret(request)

        if secret and _secret_matches(rel_object, secret):
            return True

        return rel_object.files_can_be_managed_by(request.user)


def _secret_matches(rel_object, secret: str) -> bool:
    """Check whether the presented secret belongs to the given object.

    :param rel_object: The object owning the file.
    :param secret: The secret presented by the requester.
    :returns: True if the secret matches the object's own secret.
    """
    object_secret = getattr(rel_object, "secret", None)
    if not object_secret:
        return False
    return str(object_secret) == secret


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
