from rest_framework import serializers

from toucon.models import Conference, Session, validate_date


class SessionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='v1:session-detail')

    class Meta:
        model = Session
        exclude = ('conference', 'created_at', 'organizers')
        read_only_fields = ('id', 'conference', 'updated_at')

    def validate(self, data):
        if not self.instance:
            conference = Conference.objects.get(code=self.context['view'].kwargs.get('code'))
        else:
            conference = self.instance.conference
        validate_date(data['date'], conference)
        return data
