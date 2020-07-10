from rest_framework import serializers

from evan.models import Track


class TrackSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="v1:track-detail")

    class Meta:
        model = Track
        exclude = ("event",)
        read_only_fields = ("id", "event")
