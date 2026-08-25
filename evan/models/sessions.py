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

        if self.program:
            from evan.services.program import program_service

            program_service.validate_and_sync_program_papers(self.program, session_obj=self, subsession_obj=None)
            program_service.validate_and_sync_program_keynotes(self.program, session_obj=self, subsession_obj=None)

    def clean(self) -> None:
        validate_datetime(self.start_at, self.event)
        validate_datetime(self.end_at, self.event)

        if self.room and self.room.event != self.event:
            raise ValidationError("Room is not from the same event.")

        if self.track and self.track.event != self.event:
            raise ValidationError("Track is not from the same event.")

        if self.program:
            from evan.services.program import program_service

            validation_result = program_service.validate_template(self.program, self.event.id)
            if not validation_result["is_valid"]:
                raise ValidationError({"program": validation_result["errors"]})

            self._validate_program_cross_assignments()

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
    def attendee_count(self) -> int:
        """Return the number of non-rejected registrants attending this session.

        Counts main registrants (via the ``sessions`` M2M) plus accompanying
        persons who selected this session in their registration's ``extra_data``.

        :returns: The number of attendees currently reserving a slot.
        """
        count = self.registrations.exclude(is_accepted=False).count()

        event_registrations = self.event.registrations.exclude(is_accepted=False)
        for extra_data in event_registrations.exclude(extra_data={}).values_list("extra_data", flat=True):
            for person in extra_data.get("accompanying_persons", []):
                if self.id in person.get("selected_social_events", []):
                    count += 1

        return count

    @property
    def remaining_capacity(self) -> int | None:
        """Return the number of attendee slots still available for this session.

        :returns: The remaining capacity, or None when the session is uncapped.
        """
        if not self.max_attendees:
            return None
        return max(self.max_attendees - self.attendee_count, 0)

    @property
    def is_full(self) -> bool:
        """Return whether the session has reached its configured attendee cap.

        :returns: True when the session is capped and no slots remain.
        """
        return self.remaining_capacity == 0

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

    def validate_program_template(self) -> dict[str, Any]:
        """Validate the program template and return validation results."""
        from ..services.program import program_service

        return program_service.validate_template(self.program, self.event.id)

    def get_program_paper_references(self) -> list[int]:
        """Get all paper IDs referenced in the program template."""
        from ..services.program import program_service

        return program_service.extract_paper_references(self.program)

    def get_program_keynote_references(self) -> list[str]:
        """Get all keynote codes referenced in the program template."""
        from ..services.program import program_service

        return program_service.extract_keynote_references(self.program)

    def _validate_and_sync_program_papers(self) -> None:
        """Validate and sync papers referenced in program template with session assignments."""
        from ..services.program import program_service

        program_service.validate_and_sync_program_papers(self.program, session_obj=self, subsession_obj=None)

    def _validate_and_sync_program_keynotes(self) -> None:
        """Validate and sync keynotes referenced in program template with session assignments."""
        from ..services.program import program_service

        program_service.validate_and_sync_program_keynotes(self.program, session_obj=self, subsession_obj=None)

    def _validate_program_cross_assignments(self):
        from evan.services.program import program_service

        paper_ids = program_service.extract_paper_references(self.program)
        keynote_codes = program_service.extract_keynote_references(self.program)

        if paper_ids:
            from evan.models import Paper

            queryset = Paper.objects.filter(pk__in=paper_ids, event=self.event).exclude(session=None)

            if self.pk:
                queryset = queryset.exclude(session=self)

            for paper in queryset:
                session_title = paper.session.title if paper.session else "Unknown"
                raise ValidationError({"program": f"Paper {paper.pk} is already assigned to session '{session_title}'"})

        if keynote_codes:
            from evan.models import Keynote

            queryset = Keynote.objects.filter(code__in=keynote_codes, event=self.event).exclude(session=None)

            if self.pk:
                queryset = queryset.exclude(session=self)

            for keynote in queryset:
                session_title = keynote.session.title if keynote.session else "Unknown"
                raise ValidationError(
                    {"program": f"Keynote '{keynote.code}' is already assigned to session '{session_title}'"}
                )
