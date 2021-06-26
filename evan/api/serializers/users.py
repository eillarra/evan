from django.contrib.auth import get_user_model
from django_countries.serializer_fields import CountryField
from drf_writable_nested import UniqueFieldsMixin, NestedUpdateMixin, WritableNestedModelSerializer
from rest_framework import serializers

from evan.models import Profile


class ProfileSerializer(UniqueFieldsMixin, WritableNestedModelSerializer):
    country = CountryField(country_dict=True, allow_null=True)
    custom_data = serializers.JSONField()

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
