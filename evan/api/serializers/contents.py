from rest_framework import serializers

from evan.models import Content

from .rel.files import FilesMixin


class ContentSerializer(FilesMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:content-detail")

    class Meta:  # noqa: D106
        model = Content
        exclude = ["event"]
        read_only = ["id", "key", "config"]
