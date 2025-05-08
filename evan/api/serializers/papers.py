from rest_framework import serializers

from evan.models import Paper

from .rel.files import FileSerializer, FilesMixin


class PaperReadOnlySerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:paper-detail")
    files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Paper
        exclude = ["event", "created_at", "uuid", "abstract"]


class PaperSerializer(FilesMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:paper-detail")

    class Meta:
        model = Paper
        exclude = ["event", "created_at", "uuid"]
        read_only_fields = ["id", "event", "updated_at"]


class PaperWithSecretsSerializer(PaperSerializer):
    secret_url = serializers.SerializerMethodField()

    class Meta:
        model = Paper
        exclude = ["event"]
        read_only_fields = ["id", "event", "created_at", "updated_at", "uuid", "secret"]

    def get_secret_url(self, obj):
        return obj.get_secret_url()
