import os

from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from evan.models.documents.files import BaseFileUploaderConfig
from evan.models.rel.files import File
from evan.services.file_guard import get_presented_secret
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

    def _get_uploader_config(self, content_object) -> BaseFileUploaderConfig | None:
        """Return the uploader configuration of the content object, if any.

        :param content_object: The object the file is attached to.
        :returns: The validated uploader configuration, or None.
        """
        if not hasattr(content_object, "config") or not isinstance(content_object.config, dict):
            return None

        file_uploader_config_dict = content_object.config.get("file_uploader")
        if not isinstance(file_uploader_config_dict, dict):
            return None

        try:
            return BaseFileUploaderConfig(**file_uploader_config_dict)
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

        config = self._get_uploader_config(content_object)

        if config:
            self._validate_accepted_types(data, config.accept)

            if self.instance is None and not data.get("visibility"):
                data["visibility"] = config.default_visibility

            if data.get("visibility") and data["visibility"] not in config.allowed_visibility:
                raise serializers.ValidationError(f"Visibility must be one of: {', '.join(config.allowed_visibility)}.")
        elif self.instance is None and not data.get("visibility"):
            data["visibility"] = getattr(content_object, "files_default_visibility", File.ATTENDEES)

        # An update carries only the changed fields: the file cap belongs to the
        # creation it would otherwise block.
        if self.instance is not None:
            return data

        max_files_allowed = (config.max_files if config else None) or getattr(content_object, "files_max_count", None)
        if max_files_allowed is not None and content_object.files.count() >= max_files_allowed:
            raise serializers.ValidationError(f"Maximum number of files ({max_files_allowed}) already uploaded.")

        return data

    def _validate_accepted_types(self, data, accept: str) -> None:
        """Check the uploaded file against the uploader's accepted types.

        :param data: The validated upload data.
        :param accept: The accepted types, as a comma-separated list of
            extensions or MIME types.
        :raises serializers.ValidationError: If the file's type is not accepted.
        """
        if not accept or accept == "*":
            return

        uploaded_file = data.get("file")
        if not uploaded_file:
            return

        name = getattr(uploaded_file, "name", "")
        extension = os.path.splitext(name)[1].lower()
        content_type = getattr(uploaded_file, "content_type", "") or ""

        accepted = [item.strip().lower() for item in accept.split(",") if item.strip()]
        for item in accepted:
            if item.startswith("."):
                if extension == item:
                    return
            elif item == content_type.lower():
                return

        raise serializers.ValidationError(f"File type not accepted. Allowed: {accept}")

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


class AccessibleFilesMixin(serializers.ModelSerializer):
    """Serializes related ``files``, hiding the files the viewer may not access."""

    files = serializers.SerializerMethodField()

    def get_files(self, obj):
        """Serialize the files the current request user is allowed to access.

        :param obj: The model instance with related files.
        :returns: Serialized list of accessible files.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        secret = get_presented_secret(request)
        accessible = [
            file for file in obj.files.all() if file.is_accessible_by_user(user or AnonymousUser(), secret=secret)
        ]
        return FileSerializer(accessible, many=True, context=self.context).data


class FilesMixin(AccessibleFilesMixin, serializers.ModelSerializer):
    """Addresses mixin."""

    rel_files = RelHyperlinkedField(view_name="v1:file-list")
