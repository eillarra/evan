from django.contrib.auth import get_user_model
from drf_writable_nested import UniqueFieldsMixin, NestedUpdateMixin, WritableNestedModelSerializer
from rest_framework import serializers

from evan.models import Profile
from .generic import CountryField, MetadataField


class ProfileSerializer(UniqueFieldsMixin, WritableNestedModelSerializer):
    country = CountryField(country_dict=True, allow_null=True)
    dietary = MetadataField(allow_null=True)
    gender = MetadataField(allow_null=True)

    class Meta:
        model = Profile
        exclude = ('user',)


class UserSerializer(NestedUpdateMixin, serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name', 'profile', 'url')
        read_only_fields = ('username',)
