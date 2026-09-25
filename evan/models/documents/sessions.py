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


def _format_validation_errors(exc: ValidationError) -> str:
    """Build a user-safe message from pydantic validation errors.

    Exposes only field paths and the actual validation feedback; strips
    pydantic boilerplate so raw input values and internals stay out of API
    error responses.

    :param exc: The pydantic ValidationError to format.
    :returns: A single-line, human-readable error message.
    """
    messages = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"])
        msg = error["msg"]
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        messages.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(messages)


def get_validated_session_extra_data(extra_data) -> dict:
    """Validate extra data for a session.

    :param extra_data: The raw extra data mapping to validate.
    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the extra data is not an object or fails validation."""
    if not isinstance(extra_data, dict):
        raise ValueError("Extra data must be a JSON object.")

    try:
        validated = SessionExtraData(**extra_data)
    except ValidationError as exc:
        raise ValueError(_format_validation_errors(exc)) from exc

    return json.loads(validated.model_dump_json())
