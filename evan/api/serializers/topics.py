from rest_framework import serializers

from evan.models import Topic


class TopicSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="v1:topic-detail")

    class Meta:
        model = Topic
        exclude = ("event",)
        read_only_fields = ("id", "event")
