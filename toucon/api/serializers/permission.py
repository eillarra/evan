from rest_framework import serializers

from toucon.models import Permission
from .user import BasicUserSerializer


class PermissionSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer()

    class Meta:
        model = Permission
        fields = ('user', 'level')
