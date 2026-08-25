"""Tests for list validators in evan.models and evan.models.rel."""

import pytest
from django.core.exceptions import ValidationError

from evan.models import validators as model_validators
from evan.models.rel import validators as rel_validators


@pytest.mark.parametrize(
    "module",
    [model_validators, rel_validators],
    ids=["models", "rel"],
)
class TestValidateListOfStrings:
    """Tests for validate_list_of_strings across both validator modules."""

    def test_valid_list_of_strings_passes(self, module):
        """A list of only strings does not raise."""
        module.validate_list_of_strings(["a", "b", "c"])

    def test_empty_list_passes(self, module):
        """An empty list does not raise."""
        module.validate_list_of_strings([])

    def test_non_list_value_raises(self, module):
        """A non-list value raises ValidationError."""
        with pytest.raises(ValidationError, match="Value must be a list."):
            module.validate_list_of_strings("not a list")

    def test_non_string_item_raises(self, module):
        """A list containing a non-string item raises ValidationError."""
        with pytest.raises(ValidationError, match="All items must be"):
            module.validate_list_of_strings(["a", 1, "b"])

    def test_none_raises(self, module):
        """None is not a list and raises ValidationError."""
        with pytest.raises(ValidationError, match="Value must be a list."):
            module.validate_list_of_strings(None)


@pytest.mark.parametrize(
    "module",
    [model_validators, rel_validators],
    ids=["models", "rel"],
)
class TestValidateListOfIntegers:
    """Tests for validate_list_of_integers across both validator modules."""

    def test_valid_list_of_integers_passes(self, module):
        """A list of only integers does not raise."""
        module.validate_list_of_integers([1, 2, 3])

    def test_empty_list_passes(self, module):
        """An empty list does not raise."""
        module.validate_list_of_integers([])

    def test_non_list_value_raises(self, module):
        """A non-list value raises ValidationError."""
        with pytest.raises(ValidationError, match="Value must be a list."):
            module.validate_list_of_integers(42)

    def test_non_integer_item_raises(self, module):
        """A list containing a non-integer item raises ValidationError."""
        with pytest.raises(ValidationError, match="All items must be"):
            module.validate_list_of_integers([1, "two", 3])

    def test_bool_is_accepted_as_integer(self, module):
        """Booleans are accepted because bool is a subclass of int in Python.

        This test documents the existing isinstance-based behaviour rather than
        treating it as a bug.
        """
        module.validate_list_of_integers([True, False])
