from rest_framework import serializers

from evan.models import Album

from .rel.files import FileSerializer, FilesMixin


class PhotoPairSerializer(serializers.Serializer):
    """Serializer for original + thumbnail photo pairs."""

    original = FileSerializer(read_only=True)
    thumbnail = FileSerializer(read_only=True, allow_null=True)


class AlbumSerializer(FilesMixin, serializers.ModelSerializer):
    """Album serializer."""

    files = FileSerializer(many=True, read_only=True)
    photos = PhotoPairSerializer(source="get_photo_pairs", many=True, read_only=True)
    collection_zip = FileSerializer(source="get_collection_zip", read_only=True, allow_null=True)

    class Meta:  # noqa: D106
        model = Album
        fields = ["id", "title", "files", "photos", "collection_zip"]


class AlbumListSerializer(serializers.ModelSerializer):
    """Album list serializer."""

    photo_count = serializers.SerializerMethodField()

    class Meta:  # noqa: D106
        model = Album
        fields = ["id", "title", "photo_count"]

    def get_photo_count(self, obj):
        """Get count of original photos (not including thumbnails)."""
        return obj.get_original_photos().count()
