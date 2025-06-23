import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_extra_types.color import Color


class BadgesConfig(BaseModel):
    """Badge color configuration for an event.

    Badge design, size, background (white), and content are fixed.
    Only colors for different badge types are configurable.
    """

    model_config = ConfigDict(extra="ignore", validate_default=True)

    default: Color = Field(default=Color("#2563eb"), description="Default badge color")
    guest: Color = Field(default=Color("#059669"), description="Color for guest badges")
    fee_colors: dict[str, Color] = Field(default_factory=dict, description="Colors for specific fee types")
    sort_by: Literal["first_name", "last_name"] = Field(default="first_name", description="Field to sort attendees by")
    group_by: Literal["none", "fee", "color"] = Field(default="none", description="Field to group attendees by")

    def filter_valid_fee_types(self, valid_fee_types: list[str]) -> "BadgesConfig":
        """Return a new BadgesConfig with only valid fee types.

        :param valid_fee_types: List of valid fee type strings for the event
        :returns: New BadgesConfig instance with filtered fee_colors
        """
        valid_types = set(valid_fee_types)
        filtered_fee_colors = {
            fee_type: color for fee_type, color in self.fee_colors.items() if fee_type in valid_types
        }

        return self.model_copy(update={"fee_colors": filtered_fee_colors})


def get_validated_badges_configuration(config, valid_fee_types: list[str] | None = None) -> dict:
    """Validate a badges configuration and optionally filter valid fee types.

    :param config: The badge configuration dictionary to validate
    :param valid_fee_types: Optional list of valid fee type strings to filter fee_colors
    :returns: The validated dictionary with default values and filtered fee types
    :raises ValueError: If the configuration is invalid
    """
    try:
        badges_config = BadgesConfig(**config)

        # Filter fee types if valid_fee_types is provided
        if valid_fee_types is not None:
            badges_config = badges_config.filter_valid_fee_types(valid_fee_types)

        return json.loads(badges_config.model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
