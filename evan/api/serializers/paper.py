from rest_framework import serializers

from evan.models import Paper


class PaperSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:paper-detail')

    class Meta:
        model = Paper
        exclude = ('event',)
        read_only_fields = ('id', 'event',)
