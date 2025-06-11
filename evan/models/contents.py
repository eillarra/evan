from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from .documents.contents import get_validated_content_configuration
from .rel.files import FilesMixin


class Content(FilesMixin, models.Model):
    """Content that can be used by the event website."""

    event = models.ForeignKey("evan.Event", related_name="contents", on_delete=models.CASCADE)
    key = models.CharField(max_length=32)
    value = models.TextField(default="", blank=True)

    config = models.JSONField(default=dict)

    class Meta:  # noqa: D106
        indexes = [
            models.Index(fields=["event", "key"]),
        ]
        ordering = ["event", "key"]
        unique_together = ["event", "key"]

    def __str__(self) -> str:
        return self.key

    def save(self, *args, **kwargs) -> None:
        try:
            self.config = get_validated_content_configuration(self.config or {})
        except ValueError as exc:
            raise ValidationError({"config": [str(exc)]}) from exc

        super().save(*args, **kwargs)

    def get_api_url(self) -> str:
        return reverse("v1:content-detail", args=[self.pk])

    @property
    def configuration(self) -> dict:
        return get_validated_content_configuration(self.config)
