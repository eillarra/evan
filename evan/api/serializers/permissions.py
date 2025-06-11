from rest_framework import serializers

from evan.models import Permission

from .users import BasicUserSerializer


class PermissionSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer()

    class Meta:  # noqa: D106
        model = Permission
        fields = ("user", "level")
