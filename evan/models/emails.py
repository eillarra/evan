from django.db import models

from .rel.tags import TagsMixin


class EmailTemplate(models.Model):
    """Email template for sending emails."""

    event = models.ForeignKey(
        "evan.Event", related_name="email_templates", on_delete=models.PROTECT, null=True, blank=True
    )
    code = models.CharField(max_length=64)
    from_email = models.CharField(
        "from",
        help_text="It can be a `Full Name &lt;email@domain.com&gt;` string or just an email address.",
        max_length=128,
    )
    bcc_email = models.EmailField("bcc", default="", blank=True)
    reply_to_email = models.EmailField("reply-to", default="", blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()

    action_name = models.CharField(max_length=128, help_text="This text is shown on the admin area dropdowns.")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:  # noqa: D106
        db_table = "evan_email_template"
        unique_together = ["event", "code"]

    def __str__(self) -> str:
        return self.code

    @property
    def bcc(self) -> list[str]:
        """Get bcc email address."""
        return [self.bcc_email] if self.bcc_email else []

    @property
    def reply_to(self) -> list[str]:
        """Get reply-to email address."""
        return [self.reply_to_email] if self.reply_to_email else ["evan@ugent.be"]


class EmailLog(TagsMixin, models.Model):
    """Log of sent emails."""

    event = models.ForeignKey("evan.Event", related_name="email_logs", on_delete=models.PROTECT, null=True, blank=True)
    from_email = models.CharField(max_length=255)
    to = models.JSONField(default=list)
    bcc = models.JSONField(default=list)
    reply_to = models.JSONField(default=list)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:  # noqa: D106
        db_table = "evan_log_email"

    def __str__(self) -> str:
        return f"{self.from_email} to {','.join(self.to)} - ({self.sent_at})"


class EmailPlan(models.Model):
    """A planned custom email to a filtered group of registrations.

    ``filters`` is a JSON spec resolving registrations via ``evan.services.mailer.emailplans``.
    Each sent email is logged as one :class:`EmailLog` tagged ``emailplan.id:<pk>``.
    """

    event = models.ForeignKey("evan.Event", related_name="email_plans", on_delete=models.CASCADE)
    name = models.CharField(max_length=190)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    from_email = models.CharField(max_length=128, default="UGent <evan@ugent.be>")
    bcc_email = models.EmailField(default="", blank=True)
    reply_to_email = models.EmailField(default="", blank=True)
    filters = models.JSONField(default=dict)
    send_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "evan.User", related_name="email_plans", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa: D106
        db_table = "evan_email_plan"
        ordering = ["-send_at", "-id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.event})"

    @property
    def bcc(self) -> list[str]:
        """Get bcc email addresses as a list."""
        return [self.bcc_email] if self.bcc_email else []

    @property
    def reply_to(self) -> list[str]:
        """Get reply-to email addresses as a list, falling back to the default sender."""
        return [self.reply_to_email] if self.reply_to_email else []

    @property
    def status(self) -> str:
        """Lifecycle status: ``draft``, ``scheduled``, or ``sent``."""
        if self.sent_at is not None:
            return "sent"
        if self.send_at is None:
            return "draft"
        return "scheduled"
