from django.contrib.auth import get_user_model
from rest_framework import serializers

from evan.models import Abstract, AbstractReview
from .events import EventListSerializer
from .files import FileSerializer
from .users import UserSerializer


class AbstractReviewSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:review-detail", lookup_field="id")
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=True, allow_null=False)

    class Meta:
        model = AbstractReview
        exclude = ()
        read_only_fields = ("id", "created_at", "updated_at")


class AbstractSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:abstract-detail", lookup_field="uuid")
    rel_files = serializers.HyperlinkedIdentityField(view_name="v1:abstract-files", lookup_field="uuid")
    user = UserSerializer(read_only=True)
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Abstract
        exclude = ("event",)
        read_only_fields = ("id", "uuid", "event", "is_accepted", "created_at", "updated_at")


class ManagedAbstractSerializer(AbstractSerializer):
    event = EventListSerializer(read_only=True)
    reviews = AbstractReviewSerializer(many=True, read_only=True)

    class Meta(AbstractSerializer.Meta):
        model = Abstract
        exclude = ()
        read_only_fields = ("id", "uuid", "event", "custom_data", "created_at", "updated_at")


class FullAbstractReviewSerializer(AbstractReviewSerializer):
    abstract = AbstractSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)


class PublicAbstractSerializer(AbstractSerializer):
    file = FileSerializer(read_only=True)

    class Meta:
        model = Abstract
        fields = ("id", "title", "authors", "custom_data", "abstract", "file")
