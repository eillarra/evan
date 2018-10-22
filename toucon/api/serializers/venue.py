from rest_framework import serializers

from toucon.models import Room, Venue


class RoomSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:room-detail')

    class Meta:
        model = Room
        exclude = ()
        read_only_fields = ('id',)
        write_only_fields = ('venue',)


class VenueSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:venue-detail')
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:
        model = Venue
        exclude = ('conference',)
        read_only_fields = ('id', 'conference')
