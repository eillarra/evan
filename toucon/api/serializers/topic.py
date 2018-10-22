from rest_framework import serializers

from toucon.models import Topic


class TopicSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:topic-detail')

    class Meta:
        model = Topic
        exclude = ('conference',)
        read_only_fields = ('id', 'conference')
