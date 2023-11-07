from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.parsers import FileUploadParser

from evan.models import File


class FileUploadMixin:
    max_files = None
    default_file_type = File.PUBLIC

    def get_file_type(self):
        return self.default_file_type

    @action(
        detail=True,
        methods=["post"],
        pagination_class=None,
        parser_classes=[FileUploadParser],
    )
    @method_decorator(never_cache)
    def files(self, request, *args, **kwargs):
        obj = self.get_object()

        try:
            max_files = self.max_files or obj.config["uploader"]["max_files"]
            if obj.files.count() >= max_files:
                raise ValidationError({"files": [f"You have reached the limit on number of files ({max_files})."]})
        except KeyError as exc:
            raise ValidationError({"files": ["Content is not accepting files."]}) from exc

        File(content_object=obj, type=self.get_file_type(), file=request.data["file"]).save()

        return RetrieveModelMixin.retrieve(self, request, *args, **kwargs)
