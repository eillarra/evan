from rest_framework import serializers

from evan.models import Paper

from .rel.files import FileSerializer, FilesMixin


class PaperReadOnlySerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:paper-detail")
    files = FileSerializer(many=True, read_only=True)

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
        # Let the model's clean() method handle subsession-session validation
        # Just validate that subsession belongs to the correct event if creating
        if not self.instance and "subsession" in data and data["subsession"]:
            # For new papers, ensure subsession belongs to the same event
            event_code = self.context["view"].kwargs.get("code")
            if event_code and data["subsession"].session.event.code != event_code:
                raise serializers.ValidationError("Subsession must belong to the event.")

        return data


class PaperWithSecretsSerializer(PaperSerializer):
    secret_url = serializers.SerializerMethodField()

    class Meta:  # noqa: D106
        model = Paper
        exclude = ["event"]
        read_only_fields = ["id", "event", "created_at", "updated_at", "uuid", "secret"]

    def get_secret_url(self, obj):
        return obj.get_secret_url()
