from rest_framework import serializers

from evan.models.rel.files import File

from ..base import TagsMixin
from .base import NestedRelHyperlinkField, RelHyperlinkedField


class FileSerializer(TagsMixin, serializers.ModelSerializer):
    """File serializer."""

    self = NestedRelHyperlinkField(view_name="v1:file-detail")
    url = serializers.URLField(read_only=True)

    class Meta:  # noqa: D106
        model = File
        write_only_fields = ["file"]
        exclude = ["content_type", "object_id"]


class FilesMixin(serializers.ModelSerializer):
    """Addresses mixin."""

    rel_files = RelHyperlinkedField(view_name="v1:file-list")
    files = FileSerializer(many=True, read_only=True)
