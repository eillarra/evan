"""Badge configuration documents (pydantic models).

Badge design, size and background are fixed; behaviour is configurable per
event through the ``badges`` key of ``EventExtraData``.
"""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_serializer
from pydantic_extra_types.color import Color


#: Social event badge icon keys. Keys match the social event session types;
#: each session type icon maps to a Google Material Symbols SVG file.
SOCIAL_EVENT_BADGE_ICONS: tuple[str, ...] = (
    "reception",
    "dinner",
    "beer",
    "coffee",
    "restaurant",
    "boat_trip",
    "kayaking",
    "guided_tour",
    "audio_tour",
    "castle",
    "star",
    "asterisk",
)

#: Internal key for the photo-permission camera icon (not a social event type).
CAMERA_BADGE_ICON: str = "camera"
#: Internal key for the pre-struck camera (attendee opted out of photography).
CAMERA_STRUCK_BADGE_ICON: str = "camera_struck"

#: Icon keys selectable per social event session (plus the camera).
AVAILABLE_BADGE_ICONS: tuple[str, ...] = (*SOCIAL_EVENT_BADGE_ICONS, CAMERA_BADGE_ICON)

#: Map icon keys to their Google Material Symbols SVG file name
#: (without extension) in ``evan/site/static/images/icons/``.
ICON_FILES: dict[str, str] = {
    "reception": "wine_bar",
    "dinner": "meal_dinner",
    "beer": "beer_meal",
    "coffee": "coffee",
    "restaurant": "restaurant",
    "boat_trip": "directions_boat",
    "kayaking": "kayaking",
    "guided_tour": "tour",
    "audio_tour": "headphones",
    "castle": "castle",
    "star": "kid_star",
    "asterisk": "asterisk",
    CAMERA_BADGE_ICON: "photo_camera",
    CAMERA_STRUCK_BADGE_ICON: "no_photography",
}


class BadgesConfig(BaseModel):
    """Badge configuration for an event.

    Badge design, size, background (white), and content are fixed.
    Colors, ordering, extra icons and the QR contact card are configurable.
    """

    model_config = ConfigDict(extra="ignore", validate_default=True)

    default: Color = Field(default=Color("#2563eb"), description="Default badge color")
    guest: Color = Field(default=Color("#059669"), description="Color for guest badges")
    fee_colors: dict[str, Color] = Field(default_factory=dict, description="Colors for specific fee types")

    @field_serializer("default", "guest")
    def serialize_color(self, value: Color) -> str:
        """Serialize colors as hex values.

        Pydantic's Color serializes CSS-named colors via ``as_named()`` (e.g.
        ``#0000ff`` becomes ``"blue"``), which reportlab's ``HexColor`` cannot
        parse.
        """
        return value.as_hex(format="long")

    @field_serializer("fee_colors")
    def serialize_fee_colors(self, value: dict[str, Color]) -> dict[str, str]:
        """Serialize fee colors as hex values.

        :param value: Mapping of fee type to color.
        :returns: Mapping of fee type to hex color string.
        """
        return {fee_type: color.as_hex(format="long") for fee_type, color in value.items()}

    sort_by: Literal["first_name", "last_name"] = Field(default="first_name", description="Field to sort attendees by")
    group_by: Literal["none", "fee", "color"] = Field(default="none", description="Field to group attendees by")
    show_logo: bool = Field(
        default=False,
        description="Print the event logo (an SVG file tagged 'logo') on each badge.",
    )
    icons_enabled: bool = Field(
        default=False,
        description="Show badge icons selected on social event sessions.",
    )
    show_camera_icon: bool = Field(
        default=False,
        description="Add a photo-permission camera icon that can be struck through by hand.",
    )
    qr_contact_card: bool = Field(
        default=False,
        description="Print a QR code encoding attendee contact details as a MECARD.",
    )

    def filter_valid_fee_types(self, valid_fee_types: list[str]) -> BadgesConfig:
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
