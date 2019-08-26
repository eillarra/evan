from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from evan.models import Event, Day, Fee, ImportantDate, validate_event_dates
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


class FeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fee
        exclude = ('event',)


class ImportantDateSerializer(serializers.ModelSerializer):
    date_display = serializers.CharField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)

    class Meta:
        model = ImportantDate
        exclude = ('event',)


class EventSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:event-detail', lookup_field='code')
    country = CountryField(country_dict=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    is_open_for_registration = serializers.BooleanField(read_only=True)
    days = DaySerializer(many=True, read_only=True)
    fees = FeeSerializer(many=True, read_only=True)
    dates = ImportantDateSerializer(many=True, read_only=True)
    dates_display = serializers.CharField(read_only=True)
    papers = PaperSerializer(many=True, read_only=True)
    sessions = SessionSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    venues = VenueSerializer(many=True, read_only=True)
    badge = JsonField()
    href_registration = serializers.URLField(source='get_registration_url', read_only=True)

    class Meta:
        model = Event
        exclude = ('id', 'wbs_element', 'ingenico_salt', 'test_mode', 'signature')
        read_only_fields = ('code',)

    def validate(self, data):
        validate_event_dates(Event(**data))
        return data
