import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .badges import AVAILABLE_BADGE_ICONS
from .base import Committee, ImportantDate


class SessionExtraData(BaseModel):
    """Extra data for a session."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    committees: list[Committee] = Field(default_factory=list)
    important_dates: list[ImportantDate] = Field(default_factory=list)
    group: str | None = None
    selectable_in_form: bool = False
    badge_icon: str | None = Field(default=None, description="Icon key shown on badges for this session.")

    @field_validator("group", mode="before")
    @classmethod
    def _normalize_group(cls, value: str | None) -> str | None:
        """Treat an empty string as no grouping."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("badge_icon", mode="before")
    @classmethod
    def _normalize_badge_icon(cls, value: str | None) -> str | None:
        """Treat an empty string as no icon and enforce the icon whitelist."""
        if isinstance(value, str) and not value.strip():
            return None
        if value and value not in AVAILABLE_BADGE_ICONS:
            raise ValueError(f"Unknown badge icon '{value}'. Choose one of: {', '.join(AVAILABLE_BADGE_ICONS)}.")
        return value


def get_validated_session_extra_data(extra_data) -> dict:
    """Validate extra data for a session.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the extra data is invalid."""
    try:
        return json.loads(SessionExtraData(**extra_data).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
