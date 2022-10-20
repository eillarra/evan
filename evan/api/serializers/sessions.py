from rest_framework import serializers

from evan.models import Event, Session, validate_date
from .files import FileSerializer


class SessionSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:session-detail")
    rel_files = serializers.HyperlinkedIdentityField(view_name="v1:session-files")
    files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Session
        exclude = ("event", "created_at", "organizers")
        read_only_fields = ("id", "event", "updated_at")

    def validate(self, data):
        if not self.instance:
            event = Event.objects.get(code=self.context["view"].kwargs.get("code"))
        else:
            event = self.instance.event
        validate_date(data["start_at"].date(), event)
        validate_date(data["end_at"].date(), event)
        return data
