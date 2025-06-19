"""
Centralized program template service.

This service handles all program template operations including validation
and reference extraction for both papers and keynotes.
"""

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from evan.models import Paper


class ProgramService:
    """Centralized service for program template validation and reference extraction."""

    # Pattern to match [paper:ID] references
    PAPER_PATTERN = re.compile(r"\[paper:(\d+)\]")
    # Pattern to match [paperi:ID] references (internal IDs)
    PAPER_INTERNAL_PATTERN = re.compile(r"\[paperi:([A-Za-z0-9_-]+)\]")
    # Pattern to match [keynote:CODE] references
    KEYNOTE_PATTERN = re.compile(r"\[keynote:([A-Za-z0-9_-]+)\]")

    def extract_paper_references(self, template: str) -> list[int]:
        """Extract all paper database IDs referenced in a template."""
        if not template:
            return []

        paper_ids = []

        # Extract direct database ID references [paper:ID]
        db_matches = self.PAPER_PATTERN.findall(template)
        paper_ids.extend([int(match) for match in db_matches])

        # Extract internal ID references [paperi:ID] and resolve to database IDs
        internal_matches = self.PAPER_INTERNAL_PATTERN.findall(template)
        for internal_id in internal_matches:
            try:
                # Find paper by internal_id and get its database ID
                papers = Paper.objects.filter(extra_data__internal_id=internal_id)
                if not papers.exists():
                    # Try as int
                    try:
                        internal_id_int = int(internal_id)
                        papers = Paper.objects.filter(extra_data__internal_id=internal_id_int)
                    except ValueError:
                        pass

                if papers.exists():
                    paper = papers.first()
                    if paper:
                        paper_ids.append(paper.pk)
            except Exception:
                pass  # Skip invalid internal IDs

        return list(set(paper_ids))  # Remove duplicates

    def extract_keynote_references(self, template: str) -> list[str]:
        """Extract all keynote codes referenced in a template."""
        if not template:
            return []

        # Extract keynote codes from [keynote:CODE] references
        code_matches = self.KEYNOTE_PATTERN.findall(template)
        return list(set(code_matches))  # Remove duplicates

    def validate_template(self, template: str, event_id: int | None = None) -> dict[str, Any]:
        """
        Validate a template and return validation results.

        Returns:
            Dict with 'is_valid', 'errors', 'paper_references', and 'keynote_references' keys
        """
        if not template.strip():
            return {
                "is_valid": True,
                "errors": [],
                "paper_references": [],
                "keynote_references": [],
            }

        errors = []
        paper_ids = self.extract_paper_references(template)
        keynote_codes = self.extract_keynote_references(template)

        # Validate paper references
        for paper_id in paper_ids:
            try:
                queryset = Paper.objects.select_related("session__event")
                if event_id:
                    # For papers, we need to check both assigned papers (session__event_id)
                    # and unassigned papers (event_id) to allow auto-assignment
                    queryset = queryset.filter(
                        models.Q(session__event_id=event_id) | models.Q(event_id=event_id, session__isnull=True)
                    )
                queryset.get(id=paper_id)
            except Paper.DoesNotExist:
                errors.append(f"Paper {paper_id} not found")
            except Exception as e:
                errors.append(f"Error validating paper {paper_id}: {str(e)}")

        # Validate keynote references
        for keynote_code in keynote_codes:
            try:
                from evan.models import Keynote

                queryset = Keynote.objects.select_related("event")
                if event_id:
                    queryset = queryset.filter(event_id=event_id)
                queryset.get(code=keynote_code)
            except Exception as e:
                errors.append(f"Error validating keynote {keynote_code}: {str(e)}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "paper_references": paper_ids,
            "keynote_references": keynote_codes,
        }

    def validate_and_sync_program_papers(self, program: str, session_obj, subsession_obj=None):
        """Validate and sync papers referenced in program template with assignments."""
        if not program:
            return

        paper_ids = self.extract_paper_references(program)
        if not paper_ids:
            return

        for paper_id in paper_ids:
            try:
                event_id = subsession_obj.session.event.id if subsession_obj else session_obj.event.id
                # Look for papers either assigned to sessions in this event or unassigned in this event
                paper = (
                    Paper.objects.filter(id=paper_id)
                    .filter(models.Q(session__event_id=event_id) | models.Q(event_id=event_id, session__isnull=True))
                    .first()
                )

                if not paper:
                    raise Paper.DoesNotExist()

                # Auto-assign unassigned papers
                if not paper.session and not paper.subsession:
                    if subsession_obj:
                        paper.session = subsession_obj.session
                        paper.subsession = subsession_obj
                    else:
                        paper.session = session_obj
                    paper.save()

                # Validate assignments
                elif subsession_obj and paper.subsession and paper.subsession != subsession_obj:
                    if paper.subsession.session == subsession_obj.session:
                        subsession_info = f"subsession '{paper.subsession.title}'"
                    else:
                        subsession_info = (
                            f"session '{paper.subsession.session.title}' → subsession '{paper.subsession.title}'"
                        )

                    raise ValidationError(
                        f"Paper '{paper.title}' is already assigned to {subsession_info}. "
                        f"Cannot reference it in subsession '{subsession_obj.title}' "
                        f"of session '{subsession_obj.session.title}'."
                    )

                elif not subsession_obj and paper.session and paper.session != session_obj:
                    raise ValidationError(
                        f"Paper '{paper.title}' is already assigned to session '{paper.session.title}'. "
                        f"Cannot reference it in session '{session_obj.title}'."
                    )

            except Paper.DoesNotExist as exc:
                raise ValidationError(f"Paper {paper_id} referenced in program template not found.") from exc

    def validate_and_sync_program_keynotes(self, program: str, session_obj, subsession_obj=None):
        """Validate and sync keynotes referenced in program template with assignments."""
        if not program:
            return

        keynote_codes = self.extract_keynote_references(program)
        if not keynote_codes:
            return

        from evan.models import Keynote

        for keynote_code in keynote_codes:
            try:
                event_id = subsession_obj.session.event.id if subsession_obj else session_obj.event.id
                keynote = Keynote.objects.get(code=keynote_code, event_id=event_id)

                # Auto-assign unassigned keynotes
                if not keynote.session and not keynote.subsession:
                    if subsession_obj:
                        keynote.session = subsession_obj.session
                        keynote.subsession = subsession_obj
                    else:
                        keynote.session = session_obj
                    keynote.save()

                # Validate assignments
                elif subsession_obj and keynote.subsession and keynote.subsession != subsession_obj:
                    if keynote.subsession.session == subsession_obj.session:
                        subsession_info = f"subsession '{keynote.subsession.title}'"
                    else:
                        subsession_info = (
                            f"session '{keynote.subsession.session.title}' → subsession '{keynote.subsession.title}'"
                        )

                    raise ValidationError(
                        f"Keynote '{keynote.title}' is already assigned to {subsession_info}. "
                        f"Cannot reference it in subsession '{subsession_obj.title}' "
                        f"of session '{subsession_obj.session.title}'."
                    )

                elif not subsession_obj and keynote.session and keynote.session != session_obj:
                    raise ValidationError(
                        f"Keynote '{keynote.title}' is already assigned to session '{keynote.session.title}'. "
                        f"Cannot reference it in session '{session_obj.title}'."
                    )

            except Keynote.DoesNotExist as exc:
                raise ValidationError(f"Keynote {keynote_code} referenced in program template not found.") from exc


# Global instance
program_service = ProgramService()
