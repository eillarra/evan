from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from evan.models import Coupon, Person, Registration
from .generic import MetadataField
from .user import UserSerializer


class CouponSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:coupon-detail')

    class Meta:
        model = Coupon
        exclude = ('event',)
        read_only_fields = ('id', 'code', 'event', 'created_at')


class PersonSerializer(serializers.ModelSerializer):
    dietary = MetadataField()

    class Meta:
        model = Person
        exclude = ('registration',)


class RegistrationSerializer(WritableNestedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:registration-detail', lookup_field='uuid')
    user = UserSerializer(read_only=True)
    coupon = CouponSerializer(read_only=True)
    href_payment = serializers.URLField(source='get_payment_url', read_only=True)

    class Meta:
        model = Registration
        exclude = ('id', 'event', 'saldo', 'days', 'sessions')
        read_only_fields = ('id', 'uuid', 'event', 'created_at', 'updated_at')


class RegistrationRetrieveSerializer(RegistrationSerializer):
    accompanying_persons = PersonSerializer(many=True)
    extra_fees = serializers.SerializerMethodField(read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = Registration
        exclude = ('id', 'event', 'saldo')

    def get_extra_fees(self, obj):
        return obj.event.social_event_bundle_fee * obj.accompanying_persons.count()
