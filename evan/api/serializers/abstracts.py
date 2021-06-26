from rest_framework import serializers

from evan.models import Abstract
from .events import EventListSerializer
from .files import FileSerializer
from .users import UserSerializer


class AbstractSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:abstract-detail", lookup_field="uuid")
    rel_files = serializers.HyperlinkedIdentityField(view_name="v1:abstract-files", lookup_field="uuid")
    user = UserSerializer(read_only=True)
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    files = FileSerializer(many=True, read_only=True)
    custom_data = serializers.JSONField()

    class Meta:
        model = Abstract
        exclude = ("id", "event")
        read_only_fields = ("id", "uuid", "event", "created_at", "updated_at")


class AbstractRetrieveSerializer(AbstractSerializer):
    pass


class AuthRegistrationRetrieveSerializer(AbstractRetrieveSerializer):
    event = EventListSerializer(read_only=True)

    class Meta(AbstractRetrieveSerializer.Meta):
        model = Abstract
        exclude = ("id",)
