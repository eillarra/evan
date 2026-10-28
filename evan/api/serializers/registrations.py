from rest_framework import serializers

from evan.models import Coupon, Event, Registration, Session

from .events import EventListSerializer
from .rel.remarks import RemarksMixin
from .users import UserSerializer


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for coupons."""

    self = serializers.HyperlinkedIdentityField(view_name="v1:coupon-detail")

    class Meta:  # noqa: D106
        model = Coupon
        exclude = ["event"]
        read_only_fields = ["id", "code", "event", "created_at"]


class RegistrationSerializer(RemarksMixin, serializers.ModelSerializer):
    """Serializer for registrations."""

    self = serializers.HyperlinkedIdentityField(view_name="v1:registration-detail", lookup_field="uuid")
    user = UserSerializer(read_only=True)
    is_early = serializers.BooleanField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    coupon = CouponSerializer(read_only=True)
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    payment_url = serializers.URLField(source="get_payment_url", read_only=True)
    receipt_url = serializers.URLField(source="get_receipt_url", read_only=True)
    certificate_url = serializers.URLField(source="get_certificate_url", read_only=True)
    total_fee = serializers.IntegerField(read_only=True)

    class Meta:  # noqa: D106
        model = Registration
        exclude = ["id", "event", "sessions"]
        read_only_fields = [
            "id",
            "uuid",
            "event",
            "created_at",
            "updated_at",
            "is_accepted",
            "base_fee",
            "extra_fees",
            "manual_extra_fees",
            "paid",
            "paid_via_invoice",
            "payid",
            "invoice_requested",
            "invoice_sent",
            "visa_sent",
            "no_show",
            "unique_hash",
            "saldo",
            "tags",
        ]


class RegistrationRetrieveSerializer(RegistrationSerializer):
    """Serializer for retrieving registration details."""

    # On events with the payments module disabled, registrations complete without
    # a fee type; the model-level fee resolution keeps payments-on events honest.
    fee_type = serializers.CharField(required=False, allow_blank=True)
    sessions = serializers.PrimaryKeyRelatedField(queryset=Session.objects.all(), many=True, required=False)

    def _get_event(self) -> Event:
        """Return the event this registration belongs or is being created for.

        :returns: The registration's event.
        :raises serializers.ValidationError: When the event cannot be determined.
        """
        event = self.context.get("event")
        if event is not None:
            return event

        if self.instance is not None:
            return self.instance.event

        view = self.context.get("view")
        code = getattr(view, "kwargs", {}).get("code") if view is not None else None

        if code is not None:
            try:
                return Event.objects.get(code=code)
            except Event.DoesNotExist:
                pass

        raise serializers.ValidationError("The registration's event could not be determined.")

    def validate_sessions(self, value):
        """Ensure selected sessions belong to the registration's event.

        Without this guard an attacker could link sessions from another
        event (or otherwise tamper with the M2M list) through the API.
        """
        if value is None:
            return value

        event = self._get_event()

        for session in value:
            if getattr(session, "event_id", None) != event.id:
                raise serializers.ValidationError("Sessions must belong to the registration's event.")

        return value

    def validate_extra_data(self, value):
        """Normalise accompanying-person social-event selections.

        Every ``selected_social_events`` entry must be a social-event session of
        this event. Numeric strings are converted to integers; anything else is
        rejected so all readers (fees, capacity, headcounts, badges) see ints.

        :param value: The registration extra data sent by the client.
        :returns: The normalised extra data.
        :raises serializers.ValidationError: When the data is invalid.
        """
        if value is None:
            return value

        if not isinstance(value, dict):
            raise serializers.ValidationError("Registration data must be an object.")

        if "accompanying_persons" not in value:
            return value

        persons = value["accompanying_persons"]
        if not isinstance(persons, list):
            raise serializers.ValidationError({"accompanying_persons": ["This field must be a list."]})

        if not persons:
            return value

        event = self._get_event()
        social_event_ids = set(event.sessions.filter(is_social_event=True).values_list("id", flat=True))
        normalised_persons = []

        for person in persons:
            if not isinstance(person, dict):
                raise serializers.ValidationError({"accompanying_persons": ["Each person must be an object."]})

            if "selected_social_events" not in person:
                normalised_persons.append(person)
                continue

            selected = person["selected_social_events"]
            if not isinstance(selected, list):
                raise serializers.ValidationError({"accompanying_persons": ["Selected social events must be a list."]})

            session_ids = []
            for session_id in selected:
                if isinstance(session_id, bool) or not isinstance(session_id, (int, str)):
                    raise serializers.ValidationError(
                        {"accompanying_persons": ["Selected social events must contain integer IDs."]}
                    )
                try:
                    session_id = int(session_id)
                except ValueError as exc:
                    raise serializers.ValidationError(
                        {"accompanying_persons": ["Selected social events must contain integer IDs."]}
                    ) from exc
                if session_id not in social_event_ids:
                    raise serializers.ValidationError(
                        {"accompanying_persons": ["Selected social events must be social events of this event."]}
                    )
                session_ids.append(session_id)

            normalised_persons.append({**person, "selected_social_events": session_ids})

        if not event.registration_configuration.get("accompanying_persons", True):
            current_persons = self.instance.extra_data.get("accompanying_persons", []) if self.instance else []
            if normalised_persons != current_persons:
                raise serializers.ValidationError(
                    {"accompanying_persons": ["This event does not accept accompanying persons."]}
                )

        return {**value, "accompanying_persons": normalised_persons}

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ["id", "event"]


class AuthRegistrationRetrieveSerializer(RegistrationRetrieveSerializer):
    """Serializer for authenticated users to retrieve their own registration details."""

    event = EventListSerializer(read_only=True)
    certificate_url = serializers.URLField(source="get_certificate_url", read_only=True)
    receipt_url = serializers.URLField(source="get_receipt_url", read_only=True)

    class Meta(RegistrationRetrieveSerializer.Meta):
        model = Registration
        exclude = ["id"]
