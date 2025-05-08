from rest_framework import serializers

from evan.models import Coupon, Registration

from .events import EventListSerializer
from .rel.remarks import RemarksMixin
from .users import UserTinySerializer


class CouponSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:coupon-detail")

    class Meta:
        model = Coupon
        exclude = ["event"]
        read_only_fields = ["id", "code", "event", "created_at"]


class RegistrationSerializer(RemarksMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:registration-detail", lookup_field="uuid")
    user = UserTinySerializer(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    coupon = CouponSerializer(read_only=True)
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    payment_url = serializers.URLField(source="get_payment_url", read_only=True)
    total_fee = serializers.IntegerField(read_only=True)

    class Meta:
        model = Registration
        exclude = ["id", "event", "saldo", "sessions"]
        read_only_fields = ["id", "uuid", "event", "created_at", "updated_at", "is_accepted"]


class RegistrationRetrieveSerializer(RegistrationSerializer):
    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ["id", "event", "saldo"]


class AuthRegistrationRetrieveSerializer(RegistrationRetrieveSerializer):
    event = EventListSerializer(read_only=True)
    certificate_url = serializers.URLField(source="get_certificate_url", read_only=True)
    receipt_url = serializers.URLField(source="get_receipt_url", read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ["id", "saldo"]
