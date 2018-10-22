from django.contrib.auth import get_user_model
from rest_framework import serializers

from toucon.models import Profile
from .generic import CountryField


class BasicProfileSerializer(serializers.ModelSerializer):
    country = CountryField(country_dict=True, read_only=True)

    class Meta:
        model = Profile
        exclude = ('user',)


class BasicUserSerializer(serializers.ModelSerializer):
    profile = BasicProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name', 'profile')


class ProfileSerializer(serializers.ModelSerializer):
    country = CountryField(country_dict=True)

    class Meta:
        model = Profile
        exclude = ('user',)


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:user-detail', lookup_field='username')
    profile = ProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name', 'profile', 'url')
        read_only_fields = ('username',)

    def update(self, instance, validated_data):
        super().update(instance.profile, validated_data.pop('profile'))
        return super().update(instance, validated_data)
