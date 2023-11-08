from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from evan.models import User


class AttendeeSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    country = CountryField(country_dict=True, allow_null=True)
    connect = serializers.SerializerMethodField(read_only=True)

    class Meta:  # noqa: D106
        model = User
        fields = ["id", "name", "affiliation", "country", "connect"]

    def get_connect(self, obj) -> bool:
        return obj.profile.can_be_contacted()


class UserTinySerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:  # noqa: D106
        model = User
        fields = ["username", "email", "name", "affiliation"]


class UserSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:user-detail")
    country = CountryField(country_dict=True, allow_null=True)

    class Meta:  # noqa: D106
        model = User
        fields = ["self", "id", "username", "email", "first_name", "last_name", "affiliation", "country", "is_staff"]
        read_only_fields = ["username", "is_staff"]
