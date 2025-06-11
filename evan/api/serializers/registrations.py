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
            "saldo",
        ]


class RegistrationRetrieveSerializer(RegistrationSerializer):
    """Serializer for retrieving registration details."""

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ["id", "event"]
        read_only_fields = RegistrationSerializer.Meta.read_only_fields + [
            "manual_extra_fees",
        ]


class AuthRegistrationRetrieveSerializer(RegistrationRetrieveSerializer):
    """Serializer for authenticated users to retrieve their own registration details."""

    event = EventListSerializer(read_only=True)
    certificate_url = serializers.URLField(source="get_certificate_url", read_only=True)
    receipt_url = serializers.URLField(source="get_receipt_url", read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ["id"]
