"""Tests for ``ExtraDataField`` validation of new field types and ``show_when``.

The ``form_fields`` config now supports ``radio``, ``select``, ``multiselect``,
and ``time`` field types, plus ``options`` (reusing ``FieldOption``) and a
``show_when`` pair for conditional display keyed on another field's value.
These tests verify the pydantic models accept the new shapes and reject
malformed ones.
"""

import pytest
from pydantic import ValidationError

from evan.models.documents.fees import ExtraDataField
from evan.models.documents.forms import FieldOption


class TestExtraDataFieldShape:
    """``ExtraDataField`` accepts the new field types and config keys."""

    def test_radio_field_with_options(self):
        field = ExtraDataField(
            code="arrival_day",
            label="Arrival day",
            field_type="radio",
            options=[
                FieldOption(value="saturday", label="Saturday"),
                FieldOption(value="sunday", label="Sunday"),
            ],
        )
        assert field.options is not None
        assert field.options[0].value == "saturday"

    def test_select_field_with_options(self):
        field = ExtraDataField(
            code="transport_card",
            label="Transport card",
            field_type="select",
            options=[FieldOption(value="yes", label="Yes"), FieldOption(value="no", label="No")],
        )
        assert field.field_type == "select"

    def test_multiselect_field_with_options(self):
        field = ExtraDataField(
            code="tutorials",
            label="Tutorials",
            field_type="multiselect",
            options=[FieldOption(value="chisel", label="Chisel")],
        )
        assert field.field_type == "multiselect"

    def test_time_field_without_options(self):
        field = ExtraDataField(code="arrival_time", label="Arrival time", field_type="time")
        assert field.options is None
        assert field.field_type == "time"

    def test_show_when_pair_accepted(self):
        field = ExtraDataField(
            code="arrival_time",
            label="Arrival time",
            field_type="time",
            show_when=("arrival_day", "saturday"),
        )
        assert field.show_when == ("arrival_day", "saturday")

    def test_show_when_must_be_pair(self):
        with pytest.raises(ValidationError):
            ExtraDataField(code="x", label="x", field_type="text", show_when=("arrival_day",))  # type: ignore[arg-type]

    def test_existing_text_field_unchanged(self):
        field = ExtraDataField(code="paper_id", label="Paper ID", field_type="text", required=True)
        assert field.options is None
        assert field.show_when is None
        assert field.required is True

    def test_existing_checkbox_field_unchanged(self):
        field = ExtraDataField(code="consent", label="Consent", field_type="checkbox")
        assert field.options is None
        assert field.show_for is None
