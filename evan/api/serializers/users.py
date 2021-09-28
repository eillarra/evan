from django.contrib.auth import get_user_model
from django_countries.serializer_fields import CountryField
from drf_writable_nested import UniqueFieldsMixin, NestedUpdateMixin, WritableNestedModelSerializer
from rest_framework import serializers

from evan.models import Profile


class AttendeeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    affiliation = serializers.SerializerMethodField(read_only=True)
    country = serializers.SerializerMethodField(read_only=True)
    connect = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = ("id", "name", "affiliation", "country", "connect")

    def get_affiliation(self, obj) -> str:
        return obj.profile.affiliation

    def get_connect(self, obj) -> bool:
        return obj.profile.can_be_contacted()

    def get_country(self, obj) -> str:
        return {"code": obj.profile.country.code, "name": obj.profile.country.name} if obj.profile.country else None

    def get_name(self, obj) -> str:
        return " ".join([obj.first_name, obj.last_name])


class ProfileSerializer(UniqueFieldsMixin, WritableNestedModelSerializer):
    country = CountryField(country_dict=True, allow_null=True)

    class Meta:
        model = Profile
        exclude = ("user",)


class UserSerializer(NestedUpdateMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:user-detail")
    profile = ProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = ("self", "username", "email", "first_name", "last_name", "profile")
        read_only_fields = ("username",)


class UserBasicSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:user-detail")

    class Meta:
        model = get_user_model()
        fields = ("self", "id", "username", "email", "first_name", "last_name")
