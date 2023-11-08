import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .base import ImportantDate
from .files import FileUploaderConfig
from .payments import PaymentsConfig


class EventModules(BaseModel):
    """Active modules for an event."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    abstracts: bool = Field(default=False, description="Whether the event has a simple abstract submission system")
    cms: bool = Field(default=False, description="Whether the event needs CMS options for custom website contents")


class EventConfig(BaseModel):
    """General configuration for an event."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    # active_modules: EventModules
    payments: PaymentsConfig = None
    file_uploader: FileUploaderConfig = None


class EventExtraData(BaseModel):
    """Extra data for an event."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    important_dates: list[ImportantDate] = Field(default_factory=list)


def get_validated_event_configuration(config) -> dict:
    """Validate configuration for an event.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the configuration is invalid."""
    try:
        return json.loads(EventConfig(**config).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc


def get_validated_event_extra_data(extra_data) -> dict:
    """Validate extra data for an event.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the extra data is invalid."""
    try:
        return json.loads(EventExtraData(**extra_data).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
