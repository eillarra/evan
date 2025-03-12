from rest_framework import serializers

from evan.models.venues import Room, Venue


class RoomSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:room-detail")

    class Meta:
        model = Room
        exclude = []
        read_only_fields = ["id"]
        write_only_fields = ["venue"]


class VenueReadOnlySerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:
        model = Venue
        exclude = ["event"]
        read_only_fields = ["id", "event"]


class VenueSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:venue-detail")
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:
        model = Venue
        exclude = ["event"]
        read_only_fields = ["id", "event"]
