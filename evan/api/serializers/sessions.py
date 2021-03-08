from rest_framework import serializers

from evan.models import Event, Session, validate_date


class SessionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="v1:session-detail")

    class Meta:
        model = Session
        exclude = ("event", "created_at", "organizers")
        read_only_fields = ("id", "event", "updated_at")

    def validate(self, data):
        if not self.instance:
            event = Event.objects.get(code=self.context["view"].kwargs.get("code"))
        else:
            event = self.instance.event
        validate_date(data["date"], event)
        return data
