from rest_framework import serializers

from evan.models import Coupon, Registration
from .user import BasicUserSerializer


class CouponSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:coupon-detail')

    class Meta:
        model = Coupon
        exclude = ('event',)
        read_only_fields = ('id', 'code', 'event', 'created_at')


class RegistrationSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:registration-detail', lookup_field='uuid')
    user = BasicUserSerializer(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    pending_amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = Registration
        exclude = ('id', 'event', 'invoice_sent', 'visa_sent', 'days', 'sessions')
        read_only_fields = ('id', 'uuid', 'event', 'fee', 'saldo', 'coupon', 'created_at', 'updated_at')


class RegistrationRetrieveSerializer(RegistrationSerializer):
    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ('id', 'event', 'invoice_sent', 'visa_sent')
