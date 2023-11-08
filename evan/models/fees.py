from django.db import models


class Fee(models.Model):
    """Event fees."""

    event = models.ForeignKey("evan.Event", on_delete=models.CASCADE, related_name="fees")
    type = models.CharField(max_length=16)
    value = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=190, default="", blank=True)
    is_early = models.BooleanField(default=False)
    social_events_included = models.BooleanField(default=True)

    class Meta:  # noqa: D106
        indexes = [
            models.Index(fields=["type", "is_early"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} ({self.value})"
