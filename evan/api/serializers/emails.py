from rest_framework import serializers

from evan.models.emails import EmailLog, EmailPlan
from evan.services.mailer.emailplans import resolve_recipients


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


class EmailPlanSerializer(serializers.ModelSerializer):
    """Serializer for EmailPlan with a computed recipient count.

    The ``self`` link points to the detail endpoint (``v1:emailplan-detail``).
    ``recipients_count`` is resolved lazily and cached on the instance to avoid
    recomputing the filter queryset when the field is read multiple times.
    """

    self = serializers.HyperlinkedIdentityField(view_name="v1:emailplan-detail")
    recipients_count = serializers.SerializerMethodField()

    class Meta:  # noqa: D106
        model = EmailPlan
        fields = (
            "id",
            "self",
            "name",
            "subject",
            "body",
            "from_email",
            "bcc_email",
            "reply_to_email",
            "filters",
            "send_at",
            "sent_at",
            "created_by",
            "created_at",
            "updated_at",
            "recipients_count",
        )
        read_only_fields = ("sent_at", "created_by", "created_at", "updated_at", "recipients_count")

    def get_recipients_count(self, obj: EmailPlan) -> int:
        """Return the number of registrations matching the plan's filter spec.

        :param obj: The EmailPlan instance.
        :returns: The recipient count, cached on the instance after first computation.
        """
        cache_key = "_recipients_count"
        if not hasattr(obj, cache_key):
            setattr(obj, cache_key, resolve_recipients(obj).count())
        return getattr(obj, cache_key)


class EmailPlanListSerializer(EmailPlanSerializer):
    """Lighter serializer for list views, omitting the full body."""

    class Meta(EmailPlanSerializer.Meta):  # noqa: D106
        fields = (
            "id",
            "self",
            "name",
            "subject",
            "from_email",
            "filters",
            "send_at",
            "sent_at",
            "created_at",
            "updated_at",
            "recipients_count",
        )
