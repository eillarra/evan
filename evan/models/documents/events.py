import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .badges import BadgesConfig
from .base import ImportantDate
from .fees import FeeSelectionConfig
from .files import FileUploaderConfig
from .payments import PaymentsConfig


class EventModules(BaseModel):
    """Active modules for an event."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    abstracts: bool = Field(default=False, description="Whether the event has a simple abstract submission system")
    cms: bool = Field(default=False, description="Whether the event needs CMS options for custom website contents")
    subsessions: bool = Field(default=False, description="Whether the event supports subsessions within sessions")


class EventConfig(BaseModel):
    """General configuration for an event."""

    model_config = ConfigDict(extra="ignore", validate_default=False)

    active_modules: EventModules = Field(default_factory=EventModules)
    payments: PaymentsConfig = None
    file_uploader: FileUploaderConfig = None


class EventRegistrationConfig(BaseModel):
    """Registration configuration for an event."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    fee_selection: FeeSelectionConfig = None


class EventExtraData(BaseModel):
    """Extra data for an event."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    badges: BadgesConfig = Field(default_factory=BadgesConfig, description="Badge configuration for the event")
    important_dates: list[ImportantDate] = Field(default_factory=list)
    sponsor_types: list[str] = Field(
        default_factory=list, description="Ordered list of sponsor tier names (e.g. Platinum, Gold, Silver)"
    )


def get_validated_event_configuration(config) -> dict:
    """Validate configuration for an event.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the configuration is invalid."""
    try:
        return json.loads(EventConfig(**config).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc


def get_validated_event_registration_configuration(registration_config) -> dict:
    """Validate registration configuration for an event.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the registration configuration is invalid."""
    try:
        return json.loads(EventRegistrationConfig(**registration_config).model_dump_json())
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
