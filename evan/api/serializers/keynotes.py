from rest_framework import serializers

from evan.models import Keynote

from .rel.files import FilesMixin


class KeynoteReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Keynote
        fields = ["id", "code", "title", "speaker", "bio", "abstract"]


class KeynoteSerializer(FilesMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:keynote-detail")

    class Meta:
        model = Keynote
        exclude = ["event", "created_at", "uuid"]
        read_only_fields = ["id", "event", "updated_at"]

    def validate(self, data):
        """Validate keynote data."""
        # Check that subsession belongs to session if both are provided
        if data.get("subsession") and data.get("session") and data["subsession"].session != data["session"]:
            raise serializers.ValidationError({"subsession": "Subsession must belong to the selected session."})

        # Check that session belongs to event
        if data.get("session") and data.get("event") and data["session"].event != data["event"]:
            raise serializers.ValidationError({"session": "Session must belong to the same event."})

        return data


class KeynoteWithSecretsSerializer(KeynoteSerializer):
    secret_url = serializers.SerializerMethodField()

    class Meta:  # noqa: D106
        model = Keynote
        exclude = ["event"]
        read_only_fields = ["id", "event", "created_at", "updated_at", "uuid", "secret"]

    def get_secret_url(self, obj):
        return obj.get_secret_url()
