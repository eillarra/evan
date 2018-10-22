from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from toucon.models import Conference, Day, validate_conference_dates
from .generic import JsonField
from .paper import PaperSerializer
from .session import SessionSerializer
from .topic import TopicSerializer
from .track import TrackSerializer
from .venue import VenueSerializer


class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        exclude = ('conference',)


class ConferenceSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:conference-detail', lookup_field='code')
    country = CountryField(country_dict=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    is_closed = serializers.SerializerMethodField()
    is_open_for_registration = serializers.SerializerMethodField()
    days = DaySerializer(many=True, read_only=True)
    papers = PaperSerializer(many=True, read_only=True)
    sessions = SessionSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    venues = VenueSerializer(many=True, read_only=True)
    badge = JsonField()

    class Meta:
        model = Conference
        exclude = ('id',)
        read_only_fields = ('code',)

    def get_is_active(self, obj) -> bool:
        return obj.is_active

    def get_is_closed(self, obj) -> bool:
        return obj.is_closed

    def get_is_open_for_registration(self, obj) -> bool:
        return obj.is_open_for_registration

    def validate(self, data):
        validate_conference_dates(Conference(**data))
        return data
