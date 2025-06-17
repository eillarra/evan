import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class PaperAuthor(BaseModel):
    """An extra data field for selection criteria."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    name: str
    affiliation: str | None = None


class PaperExtraData(BaseModel):
    """Extra data for a paper."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    authors_str: str | None = None
    authors: list[PaperAuthor] = Field(default_factory=list)
    internal_id: int | str | None = None


def get_validated_paper_extra_data(extra_data) -> dict:
    """Validate extra data for a paper.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the extra data is invalid."""
    try:
        return json.loads(PaperExtraData(**extra_data).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
