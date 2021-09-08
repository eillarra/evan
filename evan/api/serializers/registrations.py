from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from evan.models import Coupon, Registration
from .events import EventListSerializer
from .users import UserSerializer


class CouponSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:coupon-detail")

    class Meta:
        model = Coupon
        exclude = ("event",)
        read_only_fields = ("id", "code", "event", "created_at")


class RegistrationSerializer(WritableNestedModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:registration-detail", lookup_field="uuid")
    user = UserSerializer(read_only=True)
    coupon = CouponSerializer(read_only=True)
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    payment_url = serializers.URLField(source="get_payment_url", read_only=True)
    custom_data = serializers.JSONField()

    class Meta:
        model = Registration
        exclude = ("id", "event", "saldo", "sessions")
        read_only_fields = ("id", "uuid", "event", "created_at", "updated_at")


class RegistrationRetrieveSerializer(RegistrationSerializer):
    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ("id", "event", "saldo")


class AuthRegistrationRetrieveSerializer(RegistrationRetrieveSerializer):
    event = EventListSerializer(read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ("id", "saldo")
