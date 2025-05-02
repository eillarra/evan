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
