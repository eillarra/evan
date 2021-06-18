from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from evan.models import Event, Fee, validate_event_dates
from .sessions import SessionSerializer
from .topics import TopicSerializer
from .tracks import TrackSerializer
from .venues import VenueSerializer


class FeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fee
        exclude = ("event",)


class EventListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="v1:event-detail", lookup_field="code")
    href = serializers.URLField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Event
        fields = ("id", "code", "name", "full_name", "start_date", "end_date", "url", "href")


class EventSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="v1:event-detail", lookup_field="code")
    country = CountryField(country_dict=True, read_only=True)
    registration_early_deadline = serializers.DateTimeField(allow_null=True)
    is_active = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    is_open_for_registration = serializers.BooleanField(read_only=True)
    allows_invoices = serializers.BooleanField(read_only=True)
    fees = FeeSerializer(many=True, read_only=True)
    dates_display = serializers.CharField(read_only=True)
    sessions = SessionSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    venues = VenueSerializer(many=True, read_only=True)
    href_registration = serializers.URLField(source="get_registration_url", read_only=True)

    class Meta:
        model = Event
        exclude = ("id", "wbs_element", "ingenico_salt", "test_mode", "signature")
        read_only_fields = ("code", "custom_fields", "main_config")

    def validate(self, data):
        validate_event_dates(Event(**data))
        return data
