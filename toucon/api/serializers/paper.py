from rest_framework import serializers

from toucon.models import Paper


class PaperSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:paper-detail')

    class Meta:
        model = Paper
        exclude = ('conference',)
        read_only_fields = ('id', 'conference',)
