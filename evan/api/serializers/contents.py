from rest_framework import serializers

from evan.models import Image, Content


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("image",)


class ContentSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Content
        exclude = ("id", "event", "notes")
