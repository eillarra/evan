from rest_framework import serializers

from evan.models import Sponsor


class SponsorReadOnlySerializer(serializers.ModelSerializer):
    class Meta:  # noqa: D106
        model = Sponsor
        exclude = ["event"]


class SponsorSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:sponsor-detail")

    class Meta:  # noqa: D106
        model = Sponsor
        exclude = ["event"]
        read_only_fields = ["id", "event"]
