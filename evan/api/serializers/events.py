from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from rest_framework.reverse import reverse

from evan.models import Event, Fee, validate_event_dates

from .papers import PaperReadOnlySerializer, PaperSerializer
from .rel.files import FilesMixin
from .sessions import SessionReadOnlySerializer, SessionSerializer
from .sponsors import SponsorReadOnlySerializer, SponsorSerializer
from .topics import TopicReadOnlySerializer, TopicSerializer
from .tracks import TrackReadOnlySerializer, TrackSerializer
from .venues import VenueReadOnlySerializer, VenueSerializer


class FeeSerializer(serializers.ModelSerializer):
    """Serializer for event fees."""

    class Meta:  # noqa: D106
        model = Fee
        exclude = ["event"]


class EventListSerializer(serializers.ModelSerializer):
    """Serializer for listing events."""

    self = serializers.HyperlinkedIdentityField(view_name="v1:event-detail", lookup_field="code")
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    country = CountryField(country_dict=True, read_only=True)
    is_open_for_registration = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)

    tracks = TrackReadOnlySerializer(many=True, read_only=True)
    topics = TopicReadOnlySerializer(many=True, read_only=True)

    class Meta:  # noqa: D106
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


class EventSerializer(FilesMixin, EventListSerializer):
    """Serializer for event details."""

    # abstract_url = serializers.URLField(source="get_abstract_url", read_only=True)
    registration_url = serializers.SerializerMethodField()
    registration_early_deadline = serializers.DateTimeField(allow_null=True)
    allows_invoices = serializers.BooleanField(read_only=True)
    allows_payments = serializers.BooleanField(read_only=True)
    is_open_for_abstract_submission = serializers.BooleanField(read_only=True)
    fees = FeeSerializer(many=True, read_only=True)
    dates_display = serializers.CharField(read_only=True)

    papers = PaperReadOnlySerializer(many=True, read_only=True)
    sessions = SessionReadOnlySerializer(many=True, read_only=True)
    sponsors = SponsorReadOnlySerializer(many=True, read_only=True)
    venues = VenueReadOnlySerializer(many=True, read_only=True)

    registration_configuration = serializers.JSONField(read_only=True)

    class Meta:  # noqa: D106
        model = Event
        exclude = ["id", "accept_by_default", "signature", "config", "custom_fields"]
        read_only_fields = ["__all__"]

    def get_registration_url(self, obj) -> str | None:
        if obj.is_open_for_registration:
            return reverse(
                "registration:app",
                request=self.context.get("request"),
                kwargs={"code": obj.code},
            )
        return None


class ManagedEventSerializer(EventSerializer):
    """Serializer for managed events."""

    papers = PaperSerializer(many=True, read_only=True)
    sessions = SessionSerializer(many=True, read_only=True)
    sponsors = SponsorSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    venues = VenueSerializer(many=True, read_only=True)

    class Meta:  # noqa: D106
        model = Event
        exclude = []
        read_only_fields = ["id", "code"]

    def validate(self, data):
        validate_event_dates(Event(**data))
        return data
