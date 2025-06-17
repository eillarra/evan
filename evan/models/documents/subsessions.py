"""Subsession document validation functions."""

from typing import Any


def get_validated_subsession_extra_data(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and return subsession extra data.

    Args:
        data: Raw extra data dictionary

    Returns:
        Validated extra data dictionary

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValueError("Extra data must be a dictionary")

    # For now, we just validate that it's a dictionary
    # Future extensions can add specific field validations here
    validated_data = {}

    # Add any subsession-specific validation logic here
    # For example:
    # - Custom display options
    # - Subsession-specific metadata
    # - Integration settings

    # Copy allowed fields (for now, allow all)
    for key, value in data.items():
        if isinstance(key, str):
            validated_data[key] = value

    return validated_data
