from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import FileUploadParser
from rest_framework.viewsets import GenericViewSet

from evan.models import Content, File
from ..permissions import ContentPermission
from ..serializers import ContentSerializer
from ..viewsets import EventRelatedListOnlyViewSet


class ContentsViewSet(EventRelatedListOnlyViewSet):
    queryset = Content.objects.prefetch_related("files").all()
    pagination_class = None
    serializer_class = ContentSerializer


class ContentViewSet(UpdateModelMixin, GenericViewSet):
    permission_classes = (ContentPermission,)
    queryset = Content.objects.prefetch_related("files").all()
    serializer_class = ContentSerializer

    @action(
        detail=True,
        methods=["post"],
        pagination_class=None,
        serializer_class=ContentSerializer,
        parser_classes=[FileUploadParser],
    )
    @never_cache
    def files(self, request, *args, **kwargs):
        content = self.get_object()

        try:
            max_files = content.config["uploader"]["max_files"]
            if content.files.count() >= max_files:
                raise ValidationError({"files": [f"You have reached the limit on number of files ({max_files})."]})
        except KeyError:
            raise ValidationError({"files": ["Content is not accepting files."]})

        file = File(content_object=content, type=File.PUBLIC, file=request.data["file"])
        file.save()
        return RetrieveModelMixin.retrieve(self, request, *args, **kwargs)
