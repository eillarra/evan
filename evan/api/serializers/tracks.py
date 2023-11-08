from rest_framework import serializers

from evan.models.tracks import Track


class TrackReadOnlySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Track
        exclude = ["event"]


class TrackSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:track-detail")

    class Meta:
        model = Track
        exclude = ["event"]
        read_only_fields = ["id", "event"]
