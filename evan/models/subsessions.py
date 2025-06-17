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

        # Validate and sync program paper references
        self._validate_and_sync_program_papers()

    def get_api_url(self) -> str:
        return reverse("v1:subsession-detail", args=[self.pk])

    @property
    def date(self):
        return self.start_at.date() if self.start_at else self.session.date

    @property
    def secret(self) -> str:
        return sha256(f"{self.uuid}{settings.SECRET_KEY}".encode()).hexdigest()

    @property
    def rendered_program(self) -> str:
        if not self.program:
            return ""

        from ..utils.program_templates import program_processor

        return program_processor.process_template(self.program, self.session.event.id)

    def validate_program_template(self) -> dict:
        if not self.program:
            return {"is_valid": True, "errors": [], "paper_references": []}

        from ..utils.program_templates import program_processor

        return program_processor.validate_template(self.program, self.session.event.id)

    def get_program_paper_references(self) -> list[int]:
        if not self.program:
            return []

        from ..utils.program_templates import program_processor

        return program_processor.extract_paper_references(self.program)

    def _validate_and_sync_program_papers(self) -> None:
        """Validate and sync papers referenced in program template with subsession assignments."""
        if not self.program:
            return

        referenced_paper_ids = self.get_program_paper_references()
        if not referenced_paper_ids:
            return

        # Import here to avoid circular imports
        from .papers import Paper

        for paper_id in referenced_paper_ids:
            try:
                paper = Paper.objects.get(id=paper_id, event=self.session.event)

                # Auto-assign unassigned papers to this subsession
                if not paper.session and not paper.subsession:
                    paper.session = self.session
                    paper.subsession = self
                    paper.save()

                # Validate that assigned papers belong to this subsession
                elif paper.subsession and paper.subsession != self:
                    if paper.subsession.session == self.session:
                        subsession_info = f"subsession '{paper.subsession.title}'"
                    else:
                        subsession_info = (
                            f"session '{paper.subsession.session.title}' → subsession '{paper.subsession.title}'"
                        )

                    raise ValidationError(
                        f"Paper '{paper.title}' is already assigned to {subsession_info}. "
                        f"Cannot reference it in subsession '{self.title}'."
                    )

                # Validate that papers assigned to session (but not subsession) can't be used
                elif paper.session and paper.session != self.session:
                    raise ValidationError(
                        f"Paper '{paper.title}' is already assigned to session '{paper.session.title}'. "
                        f"Cannot reference it in subsession '{self.title}' of session '{self.session.title}'."
                    )

            except Paper.DoesNotExist as exc:
                raise ValidationError(f"Paper {paper_id} referenced in program template not found.") from exc
