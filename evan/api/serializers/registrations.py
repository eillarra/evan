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

    def validate_sessions(self, value):
        """Ensure selected sessions belong to the registration's event.

        Without this guard an attacker could link sessions from another
        event (or otherwise tamper with the M2M list) through the API.
        """
        if value is None:
            return value

        instance = self.instance

        if instance is not None:
            event = instance.event
        else:
            event = None
            view = self.context.get("view")
            code = getattr(view, "kwargs", {}).get("code") if view is not None else None

            if code is not None:
                try:
                    event = Event.objects.get(code=code)
                except Event.DoesNotExist:
                    event = None

        if event is None:
            raise serializers.ValidationError("The registration's event could not be determined.")

        for session in value:
            if getattr(session, "event_id", None) != event.id:
                raise serializers.ValidationError("Sessions must belong to the registration's event.")

        return value

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
