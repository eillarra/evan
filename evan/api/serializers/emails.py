from rest_framework import serializers

from evan.models.emails import EmailLog


class EmailListSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:email-detail")

    class Meta:  # noqa: D106
        model = EmailLog
        fields = ("id", "self", "sent_at", "subject", "to", "bcc", "reply_to", "tags")


class EmailSerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:email-detail")

    class Meta:  # noqa: D106
        model = EmailLog
        fields = "__all__"
