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

    PAPER_PATTERN = re.compile(r"\[paper:(\d+)\]")
    PAPER_INTERNAL_PATTERN = re.compile(r"\[paperi:([A-Za-z0-9_-]+)\]")
    KEYNOTE_PATTERN = re.compile(r"\[keynote:([A-Za-z0-9_-]+)\]")

    def _format_paper_description(self, paper):
        """Format paper description for error messages."""
        paper_desc = f"Paper {paper.pk}"

        internal_id = paper.extra_data.get("internal_id") if paper.extra_data else None
        if internal_id:
            paper_desc += f" (internal {internal_id})"

        return paper_desc

    def _format_subsession_description(self, subsession):
        """Format subsession description for error messages."""
        roman_numerals = {
            1: "I",
            2: "II",
            3: "III",
            4: "IV",
            5: "V",
            6: "VI",
            7: "VII",
            8: "VIII",
            9: "IX",
            10: "X",
        }
        roman = roman_numerals.get(subsession.order, str(subsession.order))

        if subsession.title:
            return f"'{subsession.title}', which is {subsession.session.code} {roman}"
        else:
            return f"'{subsession.session.code} {roman}'"

    def _format_keynote_description(self, keynote):
        """Format keynote description for error messages."""
        return f"Keynote {keynote.code}"

    def extract_paper_references(self, template: str) -> list[int]:
        """Extract all paper database IDs referenced in a template."""
        if not template:
            return []

        paper_ids = []

        db_matches = self.PAPER_PATTERN.findall(template)
        paper_ids.extend([int(match) for match in db_matches])

        internal_matches = self.PAPER_INTERNAL_PATTERN.findall(template)
        for internal_id in internal_matches:
            try:
                papers = Paper.objects.filter(extra_data__internal_id=internal_id)
                if not papers.exists():
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
                pass

        return list(set(paper_ids))

    def extract_keynote_references(self, template: str) -> list[str]:
        """Extract all keynote codes referenced in a template."""
        if not template:
            return []

        code_matches = self.KEYNOTE_PATTERN.findall(template)
        return list(set(code_matches))

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

        for paper_id in paper_ids:
            try:
                queryset = Paper.objects.select_related("session__event")
                if event_id:
                    queryset = queryset.filter(
                        models.Q(session__event_id=event_id) | models.Q(event_id=event_id, session__isnull=True)
                    )
                queryset.get(id=paper_id)
            except Paper.DoesNotExist:
                errors.append(f"Paper {paper_id} not found")
            except Exception as e:
                errors.append(f"Error validating paper {paper_id}: {str(e)}")

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

    def cleanup_orphaned_subsession_paper_assignments(self, program: str, subsession_obj):
        """
        Remove subsession assignments for papers no longer referenced in program.

        For subsessions only: removes subsession assignment but keeps session assignment.
        This allows papers to be reused in other subsessions within the same session.
        """
        if not subsession_obj:
            return

        assigned_papers = Paper.objects.filter(subsession=subsession_obj)
        referenced_paper_ids = set(self.extract_paper_references(program or ""))
        orphaned_papers = assigned_papers.exclude(id__in=referenced_paper_ids)

        for paper in orphaned_papers:
            paper.subsession = None
            paper.save(update_fields=["subsession"])

    def cleanup_orphaned_subsession_keynote_assignments(self, program: str, subsession_obj):
        """
        Remove subsession assignments for keynotes no longer referenced in program.

        For subsessions only: removes subsession assignment but keeps session assignment.
        This allows keynotes to be reused in other subsessions within the same session.
        """
        if not subsession_obj:
            return

        from evan.models import Keynote

        assigned_keynotes = Keynote.objects.filter(subsession=subsession_obj)
        referenced_keynote_codes = set(self.extract_keynote_references(program or ""))
        orphaned_keynotes = assigned_keynotes.exclude(code__in=referenced_keynote_codes)

        for keynote in orphaned_keynotes:
            keynote.subsession = None
            keynote.save(update_fields=["subsession"])

    def validate_and_sync_program_papers(self, program: str, session_obj, subsession_obj=None):
        """Validate and sync papers referenced in program template with assignments."""
        if not program:
            if subsession_obj:
                self.cleanup_orphaned_subsession_paper_assignments(program, subsession_obj)
            return

        paper_ids = self.extract_paper_references(program)

        if subsession_obj:
            self.cleanup_orphaned_subsession_paper_assignments(program, subsession_obj)

        if not paper_ids:
            return

        for paper_id in paper_ids:
            try:
                event_id = subsession_obj.session.event.id if subsession_obj else session_obj.event.id
                paper = (
                    Paper.objects.filter(id=paper_id)
                    .filter(models.Q(session__event_id=event_id) | models.Q(event_id=event_id, session__isnull=True))
                    .first()
                )

                if not paper:
                    raise Paper.DoesNotExist()

                if not paper.session and not paper.subsession:
                    if subsession_obj:
                        paper.session = subsession_obj.session
                        paper.subsession = subsession_obj
                    else:
                        paper.session = session_obj
                    paper.save()

                elif subsession_obj and paper.session == subsession_obj.session and not paper.subsession:
                    paper.subsession = subsession_obj
                    paper.save()

                elif subsession_obj and paper.subsession and paper.subsession != subsession_obj:
                    paper_desc = self._format_paper_description(paper)
                    assigned_subsession_desc = self._format_subsession_description(paper.subsession)
                    target_subsession_desc = self._format_subsession_description(subsession_obj)

                    raise ValidationError(
                        f"{paper_desc} is already assigned to subsession {assigned_subsession_desc}. "
                        f"Cannot reference it in subsession {target_subsession_desc}."
                    )

                elif not subsession_obj and paper.session and paper.session != session_obj:
                    paper_desc = self._format_paper_description(paper)
                    raise ValidationError(
                        f"{paper_desc} is already assigned to session '{paper.session.title}'. "
                        f"Cannot reference it in session '{session_obj.title}'."
                    )

                elif subsession_obj and paper.session and paper.session != subsession_obj.session:
                    paper_desc = self._format_paper_description(paper)
                    target_subsession_desc = self._format_subsession_description(subsession_obj)
                    raise ValidationError(
                        f"{paper_desc} is already assigned to session '{paper.session.title}'. "
                        f"Cannot reference it in subsession {target_subsession_desc}."
                    )

            except Paper.DoesNotExist as exc:
                raise ValidationError(f"Paper {paper_id} referenced in program template not found.") from exc

    def validate_and_sync_program_keynotes(self, program: str, session_obj, subsession_obj=None):
        """Validate and sync keynotes referenced in program template with assignments."""
        if not program:
            if subsession_obj:
                self.cleanup_orphaned_subsession_keynote_assignments(program, subsession_obj)
            return

        keynote_codes = self.extract_keynote_references(program)

        if subsession_obj:
            self.cleanup_orphaned_subsession_keynote_assignments(program, subsession_obj)

        if not keynote_codes:
            return

        from evan.models import Keynote

        for keynote_code in keynote_codes:
            try:
                event_id = subsession_obj.session.event.id if subsession_obj else session_obj.event.id
                keynote = Keynote.objects.get(code=keynote_code, event_id=event_id)

                if not keynote.session and not keynote.subsession:
                    if subsession_obj:
                        keynote.session = subsession_obj.session
                        keynote.subsession = subsession_obj
                    else:
                        keynote.session = session_obj
                    keynote.save()

                elif subsession_obj and keynote.session == subsession_obj.session and not keynote.subsession:
                    keynote.subsession = subsession_obj
                    keynote.save()

                elif subsession_obj and keynote.subsession and keynote.subsession != subsession_obj:
                    keynote_desc = self._format_keynote_description(keynote)
                    assigned_subsession_desc = self._format_subsession_description(keynote.subsession)
                    target_subsession_desc = self._format_subsession_description(subsession_obj)

                    raise ValidationError(
                        f"{keynote_desc} is already assigned to subsession {assigned_subsession_desc}. "
                        f"Cannot reference it in subsession {target_subsession_desc}."
                    )

                elif not subsession_obj and keynote.session and keynote.session != session_obj:
                    keynote_desc = self._format_keynote_description(keynote)
                    raise ValidationError(
                        f"{keynote_desc} is already assigned to session '{keynote.session.title}'. "
                        f"Cannot reference it in session '{session_obj.title}'."
                    )

                elif subsession_obj and keynote.session and keynote.session != subsession_obj.session:
                    keynote_desc = self._format_keynote_description(keynote)
                    target_subsession_desc = self._format_subsession_description(subsession_obj)
                    raise ValidationError(
                        f"{keynote_desc} is already assigned to session '{keynote.session.title}'. "
                        f"Cannot reference it in subsession {target_subsession_desc}."
                    )

            except Keynote.DoesNotExist as exc:
                raise ValidationError(f"Keynote {keynote_code} referenced in program template not found.") from exc


# Global instance
program_service = ProgramService()
