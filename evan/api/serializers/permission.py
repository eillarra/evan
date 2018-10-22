from rest_framework import serializers

from evan.models import Permission
from .user import BasicUserSerializer


class PermissionSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer()

    class Meta:
        model = Permission
        fields = ('user', 'level')
