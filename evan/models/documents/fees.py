import json

from pydantic import BaseModel, ConfigDict, ValidationError

from .forms import FieldOption


class ExtraDataField(BaseModel):
    """An extra data field for selection criteria."""

    code: str
    label: str
    field_type: str
    required: bool = False
    show_for: list[str] | None = None


class SelectionCriteria(BaseModel):
    """Generic selection criteria."""

    code: str
    question: str
    options: list[FieldOption]
    depends_on: tuple[str, list[str]] | None = None
    extra_data_fields: list[ExtraDataField] | None = None


class BaseFeeSelectionConfig(BaseModel):
    """Fee selection configuration."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    criteria: list[SelectionCriteria] = []


FeeSelectionConfig = BaseFeeSelectionConfig | None


class FeeConfig(BaseModel):
    """Fee selection configuration."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    included_social_events: list[int] = []


def get_validated_fee_configuration(config) -> dict:
    """Validate configuration for a fee.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the configuration is invalid."""
    try:
        return json.loads(FeeConfig(**config).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
