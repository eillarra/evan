from rest_framework import serializers

from evan.models import Event, Session, validate_datetime

from .rel.files import FileSerializer


class SessionReadOnlySerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:session-detail")
    files = FileSerializer(many=True, read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Session
        exclude = ["event", "created_at", "uuid", "description"]


class SessionSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:session-detail")
    files = FileSerializer(many=True, read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Session
        exclude = ["event", "created_at", "uuid"]
        read_only_fields = ["id", "event", "updated_at"]

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
    rel_files = serializers.HyperlinkedIdentityField(view_name="v1:session-files")
    secret_url = serializers.SerializerMethodField()

    class Meta:
        model = Session
        exclude = ["event"]
        read_only_fields = ["id", "event", "created_at", "updated_at", "uuid", "secret"]

    def get_secret_url(self, obj):
        return obj.get_secret_url()
