from rest_framework import serializers

from evan.models import Sponsor

from .rel.files import FileSerializer


class SponsorReadOnlySerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, read_only=True)

    class Meta:  # noqa: D106
        model = Sponsor
        exclude = ["event"]


class SponsorSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:sponsor-detail")

    class Meta:  # noqa: D106
        model = Sponsor
        exclude = ["event"]
        read_only_fields = ["id", "event"]
