from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Content

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import ContentSerializer
from ..viewsets import EventRelatedViewSet
from .files import FilesMixin


class ContentsPermission(EventRelatedPermission):
    allow_list_to_all = True
    allow_create_to_manager = True


class ContentPermission(EventRelatedObjectPermission):
    allow_update_to_manager = True
    allow_delete_to_manager = False


class ContentsViewSet(EventRelatedViewSet):
    permission_classes = [ContentsPermission]
    queryset = Content.objects.prefetch_related("files").all()
    pagination_class = None
    serializer_class = ContentSerializer


class ContentViewSet(FilesMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [ContentPermission]
    queryset = Content.objects.prefetch_related("files").all()
    serializer_class = ContentSerializer
    use_file_uploader_config = True

    def perform_update(self, serializer):
        """Remove key from validated data before updating."""
        serializer.validated_data.pop("key", None)
        serializer.save()
