from rest_framework import serializers

from evan.models.venues import Room, Venue


class RoomSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:room-detail")
    venue = serializers.PrimaryKeyRelatedField(
        queryset=Venue.objects.all(),
        required=False,  # Allow venue to be optional on updates
    )

    class Meta:  # noqa: D106
        model = Room
        exclude = []
        read_only_fields = ["id"]


class VenueReadOnlySerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:  # noqa: D106
        model = Venue
        exclude = ["event"]
        read_only_fields = ["id", "event"]


class VenueSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:venue-detail")
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:  # noqa: D106
        model = Venue
        exclude = ["event"]
        read_only_fields = ["id", "event"]
