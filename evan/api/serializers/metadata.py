from rest_framework import serializers

from evan.models import Metadata


class MetadataNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metadata
        exclude = ()


class MetadataListSerializer(MetadataNestedSerializer):
    pass
