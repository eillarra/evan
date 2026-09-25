from rest_framework import serializers

from evan.models import Coupon, Registration

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

    # Registrations are only written through the API by their attendees. Payment,
    # invoicing and attendance fields are managed by staff (admin), so every field
    # outside this allowlist is read-only, including fields added to the model later.
    attendee_writable_fields = frozenset({"fee_type", "sessions", "extra_data", "visa_requested"})

    class Meta:  # noqa: D106
        model = Registration
        exclude = ["id", "event", "sessions"]

    def get_fields(self) -> dict[str, serializers.Field]:
        """Return the serializer fields, marking every non-attendee field as read-only.

        :returns: The serializer fields, keyed by name.
        """
        fields = super().get_fields()
        for name, field in fields.items():
            if name not in self.attendee_writable_fields:
                field.read_only = True
        return fields


class RegistrationRetrieveSerializer(RegistrationSerializer):
    """Serializer for retrieving registration details."""

    # On events with the payments module disabled, registrations complete without
    # a fee type; the model-level fee resolution keeps payments-on events honest.
    fee_type = serializers.CharField(required=False, allow_blank=True)

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ["id", "event"]


class AuthRegistrationRetrieveSerializer(RegistrationRetrieveSerializer):
    """Serializer for authenticated users to retrieve their own registration details."""

    event = EventListSerializer(read_only=True)
    certificate_url = serializers.URLField(source="get_certificate_url", read_only=True)
    receipt_url = serializers.URLField(source="get_receipt_url", read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ["id"]
