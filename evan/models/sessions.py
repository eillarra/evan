from datetime import date
from hashlib import sha256
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .documents.sessions import get_validated_session_extra_data
from .rel.files import FilesMixin
from .rel.links import LinksMixin
from .rel.permissions import Permission, PermissionsMixin


def validate_datetime(dt, event) -> None:
    if dt is None:
        return
    if dt.date() < event.start_date or dt.date() > event.end_date:
        raise ValidationError("Date is not valid for this event.")


class Session(FilesMixin, LinksMixin, PermissionsMixin, models.Model):
    """A session for an event."""

    event = models.ForeignKey("evan.Event", related_name="sessions", on_delete=models.CASCADE)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    code = models.CharField(max_length=32, null=True, blank=True)  # noqa: DJ001
    title = models.CharField(max_length=190)
    description = models.TextField(default="", blank=True)
    program = models.TextField(default="", blank=True)
    max_attendees = models.PositiveSmallIntegerField(default=0, help_text="Leave on `0` for non limiting.")
    extra_attendees_fee = models.PositiveSmallIntegerField(default=0)
    is_private = models.BooleanField(default=False)
    is_social_event = models.BooleanField(default=False)

    topics = models.ManyToManyField("evan.Topic", related_name="sessions", blank=True)
    track = models.ForeignKey("evan.Track", related_name="sessions", on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey("evan.Room", related_name="sessions", on_delete=models.SET_NULL, null=True, blank=True)

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    extra_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa: D106
        ordering = ["start_at", "end_at"]
        unique_together = ["event", "code"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        try:
            self.extra_data = get_validated_session_extra_data(self.extra_data or {})
        except ValueError as exc:
            raise ValidationError({"extra_data": [str(exc)]}) from exc

        super().save(*args, **kwargs)

    def clean(self) -> None:
        validate_datetime(self.start_at, self.event)
        validate_datetime(self.end_at, self.event)

        if self.room and self.room.event != self.event:
            raise ValidationError("Room is not from the same event.")

        if self.track and self.track.event != self.event:
            raise ValidationError("Track is not from the same event.")

        # Validate and sync program paper references
        self._validate_and_sync_program_papers()

    def get_api_url(self) -> str:
        return reverse("v1:session-detail", args=[self.pk])

    def get_secret_url(self) -> str:
        return reverse("session:secret", args=[self.uuid, self.secret])

    @property
    def date(self) -> date | None:
        return self.start_at.date() if self.start_at else None

    @property
    def is_scheduled(self) -> bool:
        return self.start_at is not None and self.end_at is not None

    @property
    def secret(self) -> str:
        """A secret string for the internship."""
        return sha256(f"{self.uuid}{settings.SECRET_KEY}".encode()).hexdigest()

    @property
    def slug(self) -> str:
        return slugify(self.code) if self.code else slugify(self.title)

    def editable_by_user(self, user) -> bool:
        return user.is_staff or self.acl.filter(user_id=user.id, level__gte=Permission.ADMIN).exists()

    def files_viewable_by_user(self, user) -> bool:
        return self.editable_by_user(user) or self.event.registrations.filter(user_id=user.id).exists()

    @property
    def rendered_program(self) -> str:
        """Get the program with paper templates rendered."""
        if not self.program:
            return ""

        from ..utils.program_templates import program_processor

        return program_processor.process_template(self.program, self.event.id)

    def validate_program_template(self) -> dict[str, Any]:
        """Validate the program template and return validation results."""
        if not self.program:
            return {"is_valid": True, "errors": [], "paper_references": []}

        from ..utils.program_templates import program_processor

        return program_processor.validate_template(self.program, self.event.id)

    def get_program_paper_references(self) -> list[int]:
        """Get all paper IDs referenced in the program template."""
        if not self.program:
            return []

        from ..utils.program_templates import program_processor

        return program_processor.extract_paper_references(self.program)

    def _validate_and_sync_program_papers(self) -> None:
        """Validate and sync papers referenced in program template with session assignments."""
        if not self.program:
            return

        referenced_paper_ids = self.get_program_paper_references()
        if not referenced_paper_ids:
            return

        # Import here to avoid circular imports
        from .papers import Paper

        for paper_id in referenced_paper_ids:
            try:
                paper = Paper.objects.get(id=paper_id, event=self.event)

                # Auto-assign unassigned papers to this session
                if not paper.session and not paper.subsession:
                    paper.session = self
                    paper.save()

                # Validate that assigned papers belong to this session
                elif paper.session and paper.session != self:
                    raise ValidationError(
                        f"Paper '{paper.title}' is already assigned to session '{paper.session.title}'. "
                        f"Cannot reference it in session '{self.title}'."
                    )

            except Paper.DoesNotExist as exc:
                raise ValidationError(f"Paper {paper_id} referenced in program template not found.") from exc
