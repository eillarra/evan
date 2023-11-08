from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.viewsets import GenericViewSet

from evan.models import File

from ..permissions import FilePermission
from ..serializers import FileSerializer


class FilesMixin(RetrieveModelMixin, GenericViewSet):
    use_file_uploader_config = False

    @action(
        detail=True,
        methods=["post"],
        pagination_class=None,
        parser_classes=[FileUploadParser, MultiPartParser],
    )
    @method_decorator(never_cache)
    def files(self, request, *args, **kwargs):
        instance = self.get_object()

        if self.use_file_uploader_config and instance.configuration["file_uploader"]:
            max_files = instance.configuration["file_uploader"]["max_files"]
            if instance.files.count() >= max_files:
                raise ValidationError({"files": [f"You have reached the limit on number of files ({max_files})."]})

        # file = File(content_object=self.get_object(), type=File.PRIVATE, file=request.data["file"])
        # file.save()
        File(content_object=instance, type=File.PUBLIC, file=request.data["file"]).save()

        return self.retrieve(request, *args, **kwargs)


class FileViewSet(DestroyModelMixin, GenericViewSet):
    permission_classes = [FilePermission]
    queryset = File.objects.all()
    serializer_class = FileSerializer
