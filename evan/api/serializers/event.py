from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from evan.models import Event, Day, validate_event_dates
from .generic import JsonField
from .paper import PaperSerializer
from .session import SessionSerializer
from .topic import TopicSerializer
from .track import TrackSerializer
from .venue import VenueSerializer


class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        exclude = ('event',)


class EventSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:event-detail', lookup_field='code')
    country = CountryField(country_dict=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    is_open_for_registration = serializers.BooleanField(read_only=True)
    days = DaySerializer(many=True, read_only=True)
    papers = PaperSerializer(many=True, read_only=True)
    sessions = SessionSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    venues = VenueSerializer(many=True, read_only=True)
    badge = JsonField()

    class Meta:
        model = Event
        exclude = ('id',)
        read_only_fields = ('code',)

    def validate(self, data):
        validate_event_dates(Event(**data))
        return data
