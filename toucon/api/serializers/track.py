from rest_framework import serializers

from toucon.models import Track


class TrackSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:track-detail')

    class Meta:
        model = Track
        exclude = ('conference',)
        read_only_fields = ('id', 'conference')
