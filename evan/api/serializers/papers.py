from rest_framework import serializers

from evan.models import Paper

from .rel.files import AccessibleFilesMixin, FilesMixin


class PaperReadOnlySerializer(AccessibleFilesMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:paper-detail")

    class Meta:  # noqa: D106
        model = Paper
        exclude = ["event", "created_at", "uuid", "abstract"]


class PaperSerializer(FilesMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:paper-detail")

    class Meta:  # noqa: D106
        model = Paper
        exclude = ["event", "created_at", "uuid"]
        read_only_fields = ["id", "event", "updated_at"]

    def validate(self, data):
        """Validate paper data."""
        # Check that subsession belongs to session if both are provided
        if data.get("subsession") and data.get("session") and data["subsession"].session != data["session"]:
            raise serializers.ValidationError({"subsession": "Subsession must belong to the selected session."})

        # Check that session belongs to event
        if data.get("session") and data.get("event") and data["session"].event != data["event"]:
            raise serializers.ValidationError({"session": "Session must belong to the same event."})

        return data


class PaperWithSecretsSerializer(PaperSerializer):
    secret_url = serializers.SerializerMethodField()

    class Meta:  # noqa: D106
        model = Paper
        exclude = ["event"]
        read_only_fields = ["id", "event", "created_at", "updated_at", "uuid", "secret"]

    def get_secret_url(self, obj):
        return obj.get_secret_url()
