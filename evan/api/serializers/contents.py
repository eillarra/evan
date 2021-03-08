from rest_framework import serializers

from evan.models import Image, Content


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("image",)


class ContentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="v1:content-detail")
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        read_only = ("key", "marked", "notes")
        exclude = ("id", "event")
