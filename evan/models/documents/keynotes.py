import json

from pydantic import BaseModel, ConfigDict, ValidationError


class KeynoteExtraData(BaseModel):
    """Extra data for a keynote."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    speaker_affiliation: str | None = None
    speaker_email: str | None = None
    presentation_url: str | None = None


def get_validated_keynote_extra_data(extra_data) -> dict:
    """Validate extra data for a keynote.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the extra data is invalid."""
    try:
        return json.loads(KeynoteExtraData(**extra_data).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
