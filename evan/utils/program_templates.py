import re
from typing import Any

from evan.models import Paper


class ProgramTemplateProcessor:
    """Service to process program templates with paper references."""

    # Pattern to match [paper:ID] references
    PAPER_PATTERN = re.compile(r"\[paper:(\d+)\]")
    # Pattern to match [paperi:ID] references (internal IDs - can be alphanumeric)
    PAPER_INTERNAL_PATTERN = re.compile(r"\[paperi:([A-Za-z0-9_-]+)\]")

    def __init__(self):
        self._paper_cache = {}

    def process_template(self, template_text: str, event_id: int | None = None) -> str:
        """
        Process a template string, replacing [paper:ID] and [paperi:ID] with formatted paper info.

        Args:
            template_text: The raw template string
            event_id: Optional event ID to scope paper lookups

        Returns:
            Processed template with paper references replaced
        """
        if not template_text:
            return template_text

        def replace_paper_reference(match):
            paper_id = int(match.group(1))
            return self._format_paper_reference(paper_id, event_id)

        def replace_paper_internal_reference(match):
            internal_id = match.group(1)
            return self._format_paper_internal_reference(internal_id, event_id)

        # Process both patterns
        result = self.PAPER_PATTERN.sub(replace_paper_reference, template_text)
        result = self.PAPER_INTERNAL_PATTERN.sub(replace_paper_internal_reference, result)

        return result

    def _format_paper_reference(self, paper_id: int, event_id: int | None = None) -> str:
        try:
            paper = self._get_paper(paper_id, event_id)
            authors_str = self._format_authors(paper)

            result = f"{paper.title}"
            if authors_str:
                result += f", {authors_str}"

            if paper.doi:
                result += f" (DOI: {paper.doi})"

            return result

        except Paper.DoesNotExist:
            return f"[Paper {paper_id} not found]"
        except Exception:
            return f"[Error loading paper {paper_id}]"

    def _format_paper_internal_reference(self, internal_id: str, event_id: int | None = None) -> str:
        try:
            # Find paper by internal_id in extra_data
            queryset = Paper.objects.select_related("session__event")

            if event_id:
                # Scope to specific event through session
                queryset = queryset.filter(session__event_id=event_id)

            # Try to find paper by internal_id (could be string or int)
            papers = queryset.filter(extra_data__internal_id=internal_id)

            # If not found as string, try as int
            if not papers.exists():
                try:
                    internal_id_int = int(internal_id)
                    papers = queryset.filter(extra_data__internal_id=internal_id_int)
                except ValueError:
                    pass

            if not papers.exists():
                return f"[Paper i{internal_id} not found]"

            paper = papers.first()
            if not paper:
                return f"[Paper i{internal_id} not found]"

            authors_str = self._format_authors(paper)

            result = f"{paper.title}"
            if authors_str:
                result += f", {authors_str}"

            if paper.doi:
                result += f" (DOI: {paper.doi})"

            return result

        except Exception:
            return f"[Error loading paper i{internal_id}]"

    def _get_paper(self, paper_id: int, event_id: int | None = None) -> Paper:
        """Get paper from cache or database."""
        cache_key = f"{paper_id}_{event_id or 'any'}"

        if cache_key not in self._paper_cache:
            queryset = Paper.objects.select_related("session__event")

            if event_id:
                # Scope to specific event through session
                queryset = queryset.filter(session__event_id=event_id)

            self._paper_cache[cache_key] = queryset.get(id=paper_id)

        return self._paper_cache[cache_key]

    def _format_authors(self, paper: Paper) -> str:
        """Extract and format authors from paper.extra_data."""
        try:
            if hasattr(paper, "extra_data") and paper.extra_data:
                # Check if we have structured author data
                authors = paper.extra_data.get("authors", [])
                if authors and isinstance(authors, list):
                    return ", ".join(author.get("name", "") for author in authors if author.get("name"))

                # Fallback to authors_str if available
                authors_str = paper.extra_data.get("authors_str", "")
                if authors_str:
                    return authors_str

            return ""
        except (AttributeError, TypeError):
            return ""

    def extract_paper_references(self, template_text: str) -> list[int]:
        """Extract all paper database IDs referenced in a template (both [paper:ID] and [paperi:ID])."""
        if not template_text:
            return []

        paper_ids = []

        # Extract direct database ID references [paper:ID]
        db_matches = self.PAPER_PATTERN.findall(template_text)
        paper_ids.extend([int(match) for match in db_matches])

        # Extract internal ID references [paperi:ID] and resolve to database IDs
        internal_matches = self.PAPER_INTERNAL_PATTERN.findall(template_text)
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

    def validate_template(self, template_text: str, event_id: int | None = None) -> dict[str, Any]:
        """
        Validate a template and return validation results.

        Returns:
            Dict with 'is_valid', 'errors', and 'paper_references' keys
        """
        errors = []
        paper_ids = self.extract_paper_references(template_text)

        # Check if referenced papers exist
        for paper_id in paper_ids:
            try:
                self._get_paper(paper_id, event_id)
            except Paper.DoesNotExist:
                errors.append(f"Paper {paper_id} not found")
            except Exception as e:
                errors.append(f"Error validating paper {paper_id}: {str(e)}")

        return {"is_valid": len(errors) == 0, "errors": errors, "paper_references": paper_ids}


# Global instance
program_processor = ProgramTemplateProcessor()
