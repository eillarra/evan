from rest_framework import serializers

from evan.models import Sponsor

from .files import FileSerializer


class SponsorSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:sponsor-detail")
    rel_files = serializers.HyperlinkedIdentityField(view_name="v1:sponsor-files")
    files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Sponsor
        exclude = ("event",)
        read_only = ("id",)
