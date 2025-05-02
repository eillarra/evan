from django.core.exceptions import ValidationError
from django.db import models

from .documents.fees import get_validated_fee_configuration


class Fee(models.Model):
    """Event fees."""

    event = models.ForeignKey("evan.Event", on_delete=models.CASCADE, related_name="fees")
    type = models.CharField(max_length=64)
    early_value = models.PositiveIntegerField(null=True, blank=True)
    value = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=190, default="", blank=True)

    config = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["type"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} ({self.value})"

    def save(self, *args, **kwargs) -> None:
        try:
            self.config = get_validated_fee_configuration(self.config or {})
        except ValueError as exc:
            raise ValidationError({"config": [str(exc)]}) from exc

        super().save(*args, **kwargs)
