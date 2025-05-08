from hashlib import sha256
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from .documents.papers import get_validated_paper_extra_data
from .rel.files import FilesMixin
from .rel.links import LinksMixin
from .rel.permissions import PermissionsMixin


class Paper(FilesMixin, LinksMixin, PermissionsMixin, models.Model):
    """A paper for an event."""

    event = models.ForeignKey("evan.Event", related_name="papers", on_delete=models.CASCADE)
    title = models.CharField(max_length=190)
    abstract = models.TextField(default="", blank=True)
    doi = models.CharField(max_length=190, default="", blank=True)

    topics = models.ManyToManyField("evan.Topic", related_name="papers", blank=True)
    track = models.ForeignKey("evan.Track", related_name="papers", on_delete=models.SET_NULL, null=True, blank=True)

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    extra_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa: D106
        unique_together = ["event", "title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        try:
            self.extra_data = get_validated_paper_extra_data(self.extra_data or {})
        except ValueError as exc:
            raise ValidationError({"extra_data": [str(exc)]}) from exc

        super().save(*args, **kwargs)

    def get_api_url(self) -> str:
        return reverse("v1:paper-detail", args=[self.pk])

    def get_secret_url(self) -> str:
        return reverse("paper:secret", args=[self.uuid, self.secret])

    @property
    def secret(self) -> str:
        """A secret string for the internship."""
        return sha256(f"{self.uuid}{settings.SECRET_KEY}".encode()).hexdigest()
