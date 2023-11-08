from django.core.exceptions import ValidationError


def _validate_list(value, item_type) -> None:
    """Validate that the given value is a list of the given item type."""
    if not isinstance(value, list):
        raise ValidationError("Value must be a list.")
    for item in value:
        if not isinstance(item, item_type):
            raise ValidationError(f"All items must be `{item_type}`s.")


def validate_list_of_strings(value) -> None:
    """Validate that the given value is a list of strings."""
    _validate_list(value, str)


def validate_list_of_integers(value) -> None:
    """Validate that the given value is a list of integers."""
    _validate_list(value, int)
