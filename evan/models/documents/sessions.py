import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .base import Committee, ImportantDate


class SessionExtraData(BaseModel):
    """Extra data for a session."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    committees: list[Committee] = Field(default_factory=list)
    important_dates: list[ImportantDate] = Field(default_factory=list)


def get_validated_session_extra_data(extra_data) -> dict:
    """Validate extra data for a session.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the extra data is invalid."""
    try:
        return json.loads(SessionExtraData(**extra_data).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
