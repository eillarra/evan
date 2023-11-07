from rest_framework import serializers

from evan.models import Content

from .files import FileSerializer


class ContentSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:content-detail")
    rel_files = serializers.HyperlinkedIdentityField(view_name="v1:content-files")
    files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        exclude = ("event",)
        read_only = ("id", "key", "config")
