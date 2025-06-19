from hashlib import sha256
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from .documents.keynotes import get_validated_keynote_extra_data
from .rel.files import FilesMixin
from .rel.links import LinksMixin
from .rel.permissions import PermissionsMixin


class Keynote(FilesMixin, LinksMixin, PermissionsMixin, models.Model):
    """A keynote for an event."""

    event = models.ForeignKey("evan.Event", related_name="keynotes", on_delete=models.CASCADE)
    code = models.CharField(max_length=50, help_text="Unique identifier (e.g., K1, KEYNOTE-AI)")
    title = models.CharField(max_length=500)
    speaker = models.CharField(max_length=200, help_text="Speaker name")
    bio = models.TextField(default="", blank=True, help_text="Speaker biography")
    abstract = models.TextField(default="", blank=True, help_text="Keynote abstract or description")

    session = models.ForeignKey(
        "evan.Session", related_name="keynotes", on_delete=models.SET_NULL, null=True, blank=True
    )
    subsession = models.ForeignKey(
        "evan.Subsession", related_name="keynotes", on_delete=models.SET_NULL, null=True, blank=True
    )
    topics = models.ManyToManyField("evan.Topic", related_name="keynotes", blank=True)

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    extra_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["event", "code"]
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code}: {self.title}"

    def save(self, *args, **kwargs) -> None:
        try:
            self.extra_data = get_validated_keynote_extra_data(self.extra_data or {})
        except ValueError as exc:
            raise ValidationError({"extra_data": [str(exc)]}) from exc

        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate keynote data."""
        if self.subsession and self.subsession.session != self.session:
            raise ValidationError({"subsession": "Subsession must belong to the selected session."})

        if self.session and self.session.event != self.event:
            raise ValidationError({"session": "Session must belong to the same event."})

        if self.subsession and self.subsession.session.event != self.event:
            raise ValidationError({"subsession": "Subsession must belong to the same event."})

    def get_api_url(self) -> str:
        return reverse("v1:keynote-detail", args=[self.pk])

    def get_secret_url(self) -> str:
        # TODO: Implement keynote secret URL pattern
        return f"/keynotes/{self.uuid}/{self.secret}/"

    @property
    def secret(self) -> str:
        """A secret string for the keynote."""
        return sha256(f"{self.uuid}{settings.SECRET_KEY}".encode()).hexdigest()
