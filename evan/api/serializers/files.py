from rest_framework import serializers

from evan.models import File


class FileSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="v1:file-detail")
    href = serializers.URLField(source="get_absolute_url", read_only=True)

    class Meta:
        model = File
        fields = ("url", "href")
