from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from rest_framework.reverse import reverse

from evan.models import Event, Fee, validate_event_dates

from .rel.files import FilesMixin
from .sponsors import SponsorReadOnlySerializer, SponsorSerializer
from .topics import TopicReadOnlySerializer, TopicSerializer
from .tracks import TrackReadOnlySerializer, TrackSerializer
from .venues import VenueReadOnlySerializer, VenueSerializer


class FeeSerializer(serializers.ModelSerializer):
    """Serializer for event fees."""

    is_sold_out = serializers.SerializerMethodField()
    remaining_capacity = serializers.SerializerMethodField()

    class Meta:  # noqa: D106
        model = Fee
        exclude = ["event"]
        read_only_fields = ["is_sold_out", "remaining_capacity"]

    def _reserved_count(self, obj: Fee) -> int:
        return obj.event.registrations.exclude(is_accepted=False).filter(fee_type=obj.type).count()

    def get_remaining_capacity(self, obj: Fee) -> int | None:
        """Return the number of registrations still available for this fee type.

        :returns: The remaining capacity, or None when the fee type is uncapped.
        """
        max_registrations = obj.config.get("max_registrations")
        if not max_registrations:
            return None
        return max(max_registrations - self._reserved_count(obj), 0)

    def get_is_sold_out(self, obj: Fee) -> bool:
        """Return whether the fee type has reached its configured registration cap.

        :returns: True when the fee type is capped and no slots remain.
        """
        remaining = self.get_remaining_capacity(obj)
        return remaining == 0


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

    registration_preview_url = serializers.SerializerMethodField()

    sponsors = SponsorSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    venues = VenueSerializer(many=True, read_only=True)

    class Meta:  # noqa: D106
        model = Event
        exclude = []
        read_only_fields = ["id", "code"]

    def get_registration_preview_url(self, obj) -> str:
        """Return the absolute URL for the registration form preview.

        :returns: The absolute URL managers can visit to preview the registration form.
        """
        return reverse(
            "event:registration_preview",
            request=self.context.get("request"),
            kwargs={"code": obj.code},
        )

    def validate(self, data):
        validate_event_dates(Event(**data))
        return data
