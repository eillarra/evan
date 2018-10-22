from rest_framework import serializers

from toucon.models import Coupon, Registration
from .user import BasicUserSerializer


class CouponSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:coupon-detail')

    class Meta:
        model = Coupon
        exclude = ('conference',)
        read_only_fields = ('id', 'code', 'conference', 'created_at')


class RegistrationSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:registration-detail', lookup_field='uuid')
    user = BasicUserSerializer(read_only=True)
    is_paid = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        exclude = ('id', 'conference', 'invoice_sent', 'visa_sent', 'days', 'sessions')
        read_only_fields = ('id', 'uuid', 'conference', 'fee', 'saldo', 'coupon', 'created_at', 'updated_at')

    def get_is_paid(self, obj):
        return obj.is_paid

    def get_pending_amount(self, obj):
        return obj.pending_amount


class RegistrationRetrieveSerializer(RegistrationSerializer):
    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ('id', 'conference', 'invoice_sent', 'visa_sent')
