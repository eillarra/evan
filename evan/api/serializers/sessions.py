from rest_framework import serializers

from evan.models import Event, Session, validate_datetime

from .rel.files import FileSerializer, FilesMixin
from .subsessions import SubsessionReadOnlySerializer


class SessionReadOnlySerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:session-detail")
    files = FileSerializer(many=True, read_only=True)
    subsessions = SubsessionReadOnlySerializer(many=True, read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:  # noqa: D106
        model = Session
        exclude = ["event", "created_at", "uuid", "description", "program"]


class SessionSerializer(FilesMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:session-detail")
    subsessions = SubsessionReadOnlySerializer(many=True, read_only=True)
    slug = serializers.SlugField(read_only=True)
    rendered_program = serializers.CharField(read_only=True)

    class Meta:  # noqa: D106
        model = Session
        exclude = ["event", "created_at", "uuid", "program"]
        read_only_fields = ["id", "event", "updated_at", "rendered_program", "subsessions"]

    def validate(self, data):
        if not self.instance:
            event = Event.objects.get(code=self.context["view"].kwargs.get("code"))
        else:
            event = self.instance.event

        if "start_at" in data:
            validate_datetime(data["start_at"], event)

        if "end_at" in data:
            validate_datetime(data["end_at"], event)

        return data


class SessionWithSecretsSerializer(SessionSerializer):
    secret_url = serializers.SerializerMethodField()
    program_validation = serializers.SerializerMethodField()
    program_paper_references = serializers.SerializerMethodField()

    class Meta:  # noqa: D106
        model = Session
        exclude = ["event"]
        read_only_fields = [
            "id",
            "event",
            "created_at",
            "updated_at",
            "uuid",
            "secret",
            "rendered_program",
            "program_validation",
            "program_paper_references",
        ]

    def get_secret_url(self, obj):
        return obj.get_secret_url()

    def get_program_validation(self, obj):
        """Get program template validation results."""
        return obj.validate_program_template()

    def get_program_paper_references(self, obj):
        """Get paper IDs referenced in the program."""
        return obj.get_program_paper_references()
