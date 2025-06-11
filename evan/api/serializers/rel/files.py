from rest_framework import serializers

from evan.models.documents.files import BaseFileUploaderConfig
from evan.models.rel.files import File

from ..base import TagsMixin
from .base import NestedRelHyperlinkField, RelHyperlinkedField


class FileSerializer(TagsMixin, serializers.ModelSerializer):
    """File serializer."""

    self = NestedRelHyperlinkField(view_name="v1:file-detail")

    class Meta:  # noqa: D106
        model = File
        write_only_fields = ["file"]
        exclude = ["content_type", "object_id"]

    def _get_max_files_allowed(self, content_object):
        """Determines the maximum number of files allowed based on the content_object's configuration."""
        if not hasattr(content_object, "config") or not isinstance(content_object.config, dict):
            return None

        file_uploader_config_dict = content_object.config.get("file_uploader")
        if not isinstance(file_uploader_config_dict, dict):
            return None

        try:
            parsed_config = BaseFileUploaderConfig(**file_uploader_config_dict)
            return parsed_config.max_files
        except Exception:
            return None

    def validate(self, data):
        """Validate the incoming data for file uploads."""
        view = self.context.get("view")
        if not view:
            return data

        content_object = view.get_content_object()
        if not content_object:
            return data

        max_files_allowed = self._get_max_files_allowed(content_object)

        # Only enforce limit if explicitly configured
        if max_files_allowed is not None:
            current_file_count = content_object.files.count()
            if current_file_count >= max_files_allowed:
                raise serializers.ValidationError(f"Maximum number of files ({max_files_allowed}) already uploaded.")

        return data


class FilesMixin(serializers.ModelSerializer):
    """Addresses mixin."""

    rel_files = RelHyperlinkedField(view_name="v1:file-list")
    files = FileSerializer(many=True, read_only=True)
