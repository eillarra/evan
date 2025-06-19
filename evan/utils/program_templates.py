import re
from typing import Any

from evan.models import Paper


class ProgramTemplateProcessor:
    """Service to process program templates with paper and keynote references."""

    # Pattern to match [paper:ID] references
    PAPER_PATTERN = re.compile(r"\[paper:(\d+)\]")
    # Pattern to match [paperi:ID] references (internal IDs - can be alphanumeric)
    PAPER_INTERNAL_PATTERN = re.compile(r"\[paperi:([A-Za-z0-9_-]+)\]")
    # Pattern to match [keynote:CODE] references (using keynote codes)
    KEYNOTE_PATTERN = re.compile(r"\[keynote:([A-Za-z0-9_-]+)\]")

    def __init__(self):
        self._paper_cache = {}
        self._keynote_cache = {}

    def process_template(self, template_text: str, event_id: int | None = None) -> str:
        """
        Process a template string, replacing references with formatted info.

        Supports:
        - [paper:ID] - Paper by database ID
        - [paperi:ID] - Paper by internal ID
        - [keynote:CODE] - Keynote by code

        Args:
            template_text: The raw template string
            event_id: Optional event ID to scope lookups

        Returns:
            Processed template with references replaced
        """
        if not template_text:
            return template_text

        def replace_paper_reference(match):
            paper_id = int(match.group(1))
            return self._format_paper_reference(paper_id, event_id)

        def replace_paper_internal_reference(match):
            internal_id = match.group(1)
            return self._format_paper_internal_reference(internal_id, event_id)

        def replace_keynote_reference(match):
            keynote_code = match.group(1)
            return self._format_keynote_reference(keynote_code, event_id)

        # Process all patterns
        result = self.PAPER_PATTERN.sub(replace_paper_reference, template_text)
        result = self.PAPER_INTERNAL_PATTERN.sub(replace_paper_internal_reference, result)
        result = self.KEYNOTE_PATTERN.sub(replace_keynote_reference, result)

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

    def _format_keynote_reference(self, keynote_code: str, event_id: int | None = None) -> str:
        """Format a keynote reference by code."""
        try:
            keynote = self._get_keynote_by_code(keynote_code, event_id)
            return f"{keynote.title} - {keynote.speaker}"
        except Exception:
            return f"[Keynote {keynote_code} not found]"

    def _get_keynote_by_code(self, keynote_code: str, event_id: int | None = None):
        """Get keynote by code from cache or database."""
        from evan.models import Keynote

        cache_key = f"keynote_code_{keynote_code}_{event_id or 'any'}"

        if cache_key not in self._keynote_cache:
            queryset = Keynote.objects.select_related("event")

            if event_id:
                queryset = queryset.filter(event_id=event_id)

            self._keynote_cache[cache_key] = queryset.get(code=keynote_code)

        return self._keynote_cache[cache_key]

    def _get_keynote(self, keynote_id: int, event_id: int | None = None):
        """Get keynote from cache or database."""
        from evan.models import Keynote

        cache_key = f"keynote_{keynote_id}_{event_id or 'any'}"

        if cache_key not in self._keynote_cache:
            queryset = Keynote.objects.select_related("event")

            if event_id:
                queryset = queryset.filter(event_id=event_id)

            self._keynote_cache[cache_key] = queryset.get(id=keynote_id)

        return self._keynote_cache[cache_key]

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

    def extract_keynote_references(self, template_text: str) -> list[str]:
        """Extract all keynote codes referenced in a template."""
        if not template_text:
            return []

        # Extract keynote codes from [keynote:CODE] references
        code_matches = self.KEYNOTE_PATTERN.findall(template_text)
        return list(set(code_matches))  # Remove duplicates

    def validate_template(self, template_text: str, event_id: int | None = None) -> dict[str, Any]:
        """
        Validate a template and return validation results.

        Returns:
            Dict with 'is_valid', 'errors', 'paper_references', and 'keynote_references' keys
        """
        errors = []
        paper_ids = self.extract_paper_references(template_text)
        keynote_codes = self.extract_keynote_references(template_text)

        # Check if referenced papers exist
        for paper_id in paper_ids:
            try:
                self._get_paper(paper_id, event_id)
            except Paper.DoesNotExist:
                errors.append(f"Paper {paper_id} not found")
            except Exception as e:
                errors.append(f"Error validating paper {paper_id}: {str(e)}")

        # Check if referenced keynotes exist
        for keynote_code in keynote_codes:
            try:
                self._get_keynote_by_code(keynote_code, event_id)
            except Exception as e:
                errors.append(f"Error validating keynote {keynote_code}: {str(e)}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "paper_references": paper_ids,
            "keynote_references": keynote_codes,
        }


# Global instance
program_processor = ProgramTemplateProcessor()
