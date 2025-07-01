import os

from rest_framework import serializers

from evan.models.documents.files import BaseFileUploaderConfig
from evan.models.rel.files import File
from evan.services.image_processor import ImageProcessor

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

    def create(self, validated_data):
        """Create a new file instance with image processing if applicable."""
        # Process image if it's an image file
        uploaded_file = validated_data.get("file")
        tags = validated_data.get("tags", [])

        if uploaded_file and ImageProcessor.should_process_image(uploaded_file.name, tags):
            # Process the image and replace the uploaded file
            processed_file = ImageProcessor.process_image(uploaded_file, tags)
            validated_data["file"] = processed_file

            # Update description to reflect new extension if needed
            original_description = validated_data.get("description", "")
            if original_description:
                # Extract extensions
                original_ext = os.path.splitext(uploaded_file.name)[1].lower()
                new_ext = os.path.splitext(processed_file.name)[1].lower()

                # If extensions differ and description ends with the original extension,
                # replace it with the new extension
                if original_ext != new_ext and original_description.lower().endswith(original_ext):
                    validated_data["description"] = original_description[: -len(original_ext)] + new_ext

        return super().create(validated_data)


class FilesMixin(serializers.ModelSerializer):
    """Addresses mixin."""

    rel_files = RelHyperlinkedField(view_name="v1:file-list")
    files = FileSerializer(many=True, read_only=True)
