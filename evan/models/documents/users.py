import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class UserExtraData(BaseModel):
    """Extra data for a user."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    gender: Literal["none", "male", "female", "non_binary", "prefer_not_to_say"] = Field(
        default="none", description="Gender of the user"
    )
    dietary: str = Field(default="none", description="Dietary requirements of the user")
    special_needs: str | None = Field(default=None, description="Special needs of the user")
    connect: bool = Field(default=True, description="Whether the user can be contacted")


def get_validated_extra_data(config) -> dict:
    """Validate extra data for a user.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the configuration is invalid."""
    try:
        return json.loads(UserExtraData(**config).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc
