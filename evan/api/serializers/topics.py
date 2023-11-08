from rest_framework import serializers

from evan.models.topics import Topic


class TopicReadOnlySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Topic
        exclude = ["event"]


class TopicSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:topic-detail")

    class Meta:
        model = Topic
        exclude = ["event"]
        read_only_fields = ["id", "event"]
