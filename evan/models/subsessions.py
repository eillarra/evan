from hashlib import sha256
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Subsession(models.Model):
    """A subsession within a session for more detailed scheduling."""

    session = models.ForeignKey("evan.Session", related_name="subsessions", on_delete=models.CASCADE)
    title = models.CharField(max_length=190, default="", blank=True)
    program = models.TextField(default="", blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["session", "order", "start_at"]
        unique_together = ["session", "order"]

    def __str__(self) -> str:
        return f"{self.session.title} - {self.title}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        # Always call program service, even for empty programs (to handle cleanup)
        from evan.services.program import program_service

        program_service.validate_and_sync_program_papers(self.program, session_obj=self.session, subsession_obj=self)
        program_service.validate_and_sync_program_keynotes(self.program, session_obj=self.session, subsession_obj=self)

    def clean(self) -> None:
        if self.start_at and self.session.start_at and self.start_at < self.session.start_at:
            raise ValidationError({"start_at": "Subsession start time cannot be before session start time."})

        if self.end_at and self.session.end_at and self.end_at > self.session.end_at:
            raise ValidationError({"end_at": "Subsession end time cannot be after session end time."})

        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError({"start_at": "Subsession start time must be before end time."})

        if self.start_at and not self.session.start_at:
            raise ValidationError({"start_at": "Cannot set subsession start time when session has no start time."})

        if self.end_at and not self.session.end_at:
            raise ValidationError({"end_at": "Cannot set subsession end time when session has no end time."})

        if self.program:
            from evan.services.program import program_service

            validation_result = program_service.validate_template(self.program, self.session.event.id)
            if not validation_result["is_valid"]:
                raise ValidationError({"program": validation_result["errors"]})

            self._validate_program_cross_assignments()

    def get_api_url(self) -> str:
        return reverse("v1:subsession-detail", args=[self.pk])

    @property
    def date(self):
        return self.start_at.date() if self.start_at else self.session.date

    @property
    def secret(self) -> str:
        return sha256(f"{self.uuid}{settings.SECRET_KEY}".encode()).hexdigest()

    def validate_program_template(self) -> dict:
        from ..services.program import program_service

        return program_service.validate_template(self.program, self.session.event.id)

    def get_program_paper_references(self) -> list[int]:
        from ..services.program import program_service

        return program_service.extract_paper_references(self.program)

    def get_program_keynote_references(self) -> list[str]:
        from ..services.program import program_service

        return program_service.extract_keynote_references(self.program)

    def _validate_and_sync_program_papers(self) -> None:
        """Validate and sync papers referenced in program template with subsession assignments."""
        from ..services.program import program_service

        program_service.validate_and_sync_program_papers(self.program, session_obj=self.session, subsession_obj=self)

    def _validate_and_sync_program_keynotes(self) -> None:
        """Validate and sync keynotes referenced in program template with subsession assignments."""
        from ..services.program import program_service

        program_service.validate_and_sync_program_keynotes(self.program, session_obj=self.session, subsession_obj=self)

    def _validate_program_cross_assignments(self):
        from evan.services.program import program_service

        paper_ids = program_service.extract_paper_references(self.program)
        keynote_codes = program_service.extract_keynote_references(self.program)

        if paper_ids:
            from evan.models import Paper

            queryset = Paper.objects.filter(pk__in=paper_ids, event=self.session.event).exclude(session=None)

            if self.pk:
                queryset = queryset.exclude(subsession=self)

            for paper in queryset:
                # Block papers assigned to different sessions
                if paper.session != self.session:
                    paper_desc = program_service._format_paper_description(paper)
                    session_title = paper.session.title if paper.session else "Unknown"
                    raise ValidationError({"program": f"{paper_desc} is already assigned to session '{session_title}'"})

                # Block papers assigned to different subsessions (within same session)
                if paper.subsession and paper.subsession != self:
                    paper_desc = program_service._format_paper_description(paper)
                    assigned_subsession_desc = program_service._format_subsession_description(paper.subsession)
                    target_subsession_desc = program_service._format_subsession_description(self)
                    raise ValidationError(
                        {
                            "program": f"{paper_desc} is already assigned to subsession {assigned_subsession_desc}. "
                            f"Cannot reference it in subsession {target_subsession_desc}."
                        }
                    )

        if keynote_codes:
            from evan.models import Keynote

            queryset = Keynote.objects.filter(code__in=keynote_codes, event=self.session.event).exclude(session=None)

            if self.pk:
                queryset = queryset.exclude(subsession=self)

            for keynote in queryset:
                # Block keynotes assigned to different sessions
                if keynote.session != self.session:
                    keynote_desc = program_service._format_keynote_description(keynote)
                    session_title = keynote.session.title if keynote.session else "Unknown"
                    raise ValidationError(
                        {"program": f"{keynote_desc} is already assigned to session '{session_title}'"}
                    )

                # Block keynotes assigned to different subsessions (within same session)
                if keynote.subsession and keynote.subsession != self:
                    keynote_desc = program_service._format_keynote_description(keynote)
                    assigned_subsession_desc = program_service._format_subsession_description(keynote.subsession)
                    target_subsession_desc = program_service._format_subsession_description(self)
                    raise ValidationError(
                        {
                            "program": f"{keynote_desc} is already assigned to subsession {assigned_subsession_desc}. "
                            f"Cannot reference it in subsession {target_subsession_desc}."
                        }
                    )
