from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from evan.models import Event, Fee, validate_event_dates

from .rel.files import FileSerializer
from .sessions import SessionReadOnlySerializer, SessionSerializer
from .sponsors import SponsorReadOnlySerializer, SponsorSerializer
from .topics import TopicReadOnlySerializer, TopicSerializer
from .tracks import TrackReadOnlySerializer, TrackSerializer
from .venues import VenueReadOnlySerializer, VenueSerializer


class FeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fee
        exclude = ["event"]


class EventListSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:event-detail", lookup_field="code")
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    country = CountryField(country_dict=True, read_only=True)
    is_open_for_registration = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)

    tracks = TrackReadOnlySerializer(many=True, read_only=True)
    topics = TopicReadOnlySerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "self",
            "code",
            "name",
            "full_name",
            "start_date",
            "end_date",
            "url",
            "city",
            "country",
            "registrations_count",
            "is_open_for_registration",
            "is_active",
            "is_closed",
            "tracks",
            "topics",
            "website",
        ]


class EventSerializer(EventListSerializer):
    rel_files = serializers.HyperlinkedIdentityField(view_name="v1:event-files", lookup_field="code")
    # abstract_url = serializers.URLField(source="get_abstract_url", read_only=True)
    # registration_url = serializers.URLField(source="get_registration_url", read_only=True)
    registration_early_deadline = serializers.DateTimeField(allow_null=True)
    allows_invoices = serializers.BooleanField(read_only=True)
    allows_payments = serializers.BooleanField(read_only=True)
    is_open_for_abstract_submission = serializers.BooleanField(read_only=True)
    fees = FeeSerializer(many=True, read_only=True)
    dates_display = serializers.CharField(read_only=True)
    files = FileSerializer(many=True, read_only=True)

    sessions = SessionReadOnlySerializer(many=True, read_only=True)
    sponsors = SponsorReadOnlySerializer(many=True, read_only=True)
    venues = VenueReadOnlySerializer(many=True, read_only=True)

    registration_configuration = serializers.JSONField(read_only=True)

    class Meta:
        model = Event
        exclude = ["id", "accept_by_default", "signature", "config", "custom_fields"]
        read_only_fields = ["__all__"]


class ManagedEventSerializer(EventSerializer):
    sessions = SessionSerializer(many=True, read_only=True)
    sponsors = SponsorSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    venues = VenueSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        exclude = []
        read_only_fields = ["id", "code"]

    def validate(self, data):
        validate_event_dates(Event(**data))
        return data
