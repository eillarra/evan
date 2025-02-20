from pydantic import BaseModel, ConfigDict


class FieldOption(BaseModel):
    """An option for a choice field."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    value: str | int
    label: str
    description: str | None = None
    is_default: bool = False
