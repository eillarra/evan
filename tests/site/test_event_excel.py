"""Tests for event registration Excel exports."""

import json

from evan.site.views.events import get_registration_sheets
from tests._factories import RegistrationFactory, UserFactory


def test_registration_excel_includes_configured_extra_fields(t_event) -> None:
    """Configured registration form fields are exported in the registrations sheet."""
    t_event.registration_config = {
        "form_fields": [
            {"code": "institution_type", "label": "Institution type", "field_type": "select", "required": False},
            {"code": "paper_id", "label": "Paper ID", "field_type": "text", "required": False},
        ]
    }
    t_event.save()

    registration = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        extra_data={"institution_type": "university", "paper_id": "P-123"},
    )

    sheets = get_registration_sheets(t_event)
    registrations_sheet = next(df for df, name in sheets if name == "REGISTRATIONS")
    row = next(item for item in registrations_sheet.to_dicts() if item["uuid"] == str(registration.uuid))

    assert "institution_type" in registrations_sheet.columns
    assert "paper_id" in registrations_sheet.columns
    assert row["institution_type"] == "university"
    assert row["paper_id"] == "P-123"


def test_registration_excel_serializes_complex_extra_field_values(t_event) -> None:
    """List and object extra values are serialized as JSON strings in Excel rows."""
    t_event.registration_config = {
        "form_fields": [
            {
                "code": "selected_tracks",
                "label": "Selected tracks",
                "field_type": "checkbox",
                "required": False,
            },
            {"code": "metadata", "label": "Metadata", "field_type": "text", "required": False},
        ]
    }
    t_event.save()

    RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        extra_data={"selected_tracks": ["ai", "ethics"], "metadata": {"needs_invoice": True}},
    )

    sheets = get_registration_sheets(t_event)
    registrations_sheet = next(df for df, name in sheets if name == "REGISTRATIONS")
    row = registrations_sheet.to_dicts()[0]

    assert row["selected_tracks"] == json.dumps(["ai", "ethics"], ensure_ascii=False)
    assert row["metadata"] == json.dumps({"needs_invoice": True}, ensure_ascii=False)
