from rest_framework import serializers

from evan.models.rel.files import File


class FileSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:file-detail")
    url = serializers.FileField(source="file")

    class Meta:  # noqa: D106
        model = File
        fields = ["self", "url", "type", "tags"]
