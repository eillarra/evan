from pydantic import BaseModel, ConfigDict

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
