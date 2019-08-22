from rest_framework import serializers

from evan.models import Content


class ContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Content
        exclude = ('event',)
