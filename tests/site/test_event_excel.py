"""Tests for event registration Excel exports."""

import json
from http import HTTPStatus as status
from typing import Any, NoReturn

import pytest
from django.urls import reverse

from evan.site.views.events import get_registration_sheets
from tests._factories import RegistrationFactory, SessionFactory, UserFactory


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


def test_registration_excel_includes_sponsor_email_consent(t_event) -> None:
    """Sponsor email consent from ``_internal`` extra data is exported in the registrations sheet."""
    consented = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        extra_data={"_internal": {"share_email_with_sponsors": True}},
    )
    opted_out = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        extra_data={},
    )

    sheets = get_registration_sheets(t_event)
    registrations_sheet = next(df for df, name in sheets if name == "REGISTRATIONS")
    rows = {row["uuid"]: row for row in registrations_sheet.to_dicts()}

    assert "share_email_with_sponsors" in registrations_sheet.columns
    assert rows[str(consented.uuid)]["share_email_with_sponsors"] is True
    assert rows[str(opted_out.uuid)]["share_email_with_sponsors"] is False


def test_registration_excel_includes_photo_consent(t_event) -> None:
    """Photo consent from ``_internal`` extra data is exported in the registrations sheet."""
    opted_out = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        extra_data={"_internal": {"allow_photo_sharing": False}},
    )
    allowed = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        extra_data={"_internal": {"allow_photo_sharing": True}},
    )
    not_asked = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        extra_data={},
    )

    sheets = get_registration_sheets(t_event)
    registrations_sheet = next(df for df, name in sheets if name == "REGISTRATIONS")
    rows = {row["uuid"]: row for row in registrations_sheet.to_dicts()}

    assert "allow_photo_sharing" in registrations_sheet.columns
    assert rows[str(opted_out.uuid)]["allow_photo_sharing"] is False
    assert rows[str(allowed.uuid)]["allow_photo_sharing"] is True
    assert rows[str(not_asked.uuid)]["allow_photo_sharing"] is True


def test_registration_excel_omits_photo_consent_for_virtual_events(t_event) -> None:
    """Virtual events never ask the photo consent question, so the column is blank."""
    t_event.is_virtual = True
    t_event.save()

    registration = RegistrationFactory(event=t_event, user=UserFactory(), is_accepted=True)

    sheets = get_registration_sheets(t_event)
    registrations_sheet = next(df for df, name in sheets if name == "REGISTRATIONS")
    row = registrations_sheet.to_dicts()[0]

    assert row["uuid"] == str(registration.uuid)
    assert row["allow_photo_sharing"] is None


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


def test_registration_excel_includes_program_session_sheets(t_event) -> None:
    """A ``selectable_in_form`` program session produces a PROGRAM sheet with its registrants."""
    program_session = SessionFactory(
        event=t_event,
        title="Parallel track A",
        is_social_event=False,
        is_private=False,
        extra_data={"selectable_in_form": True},
    )
    registration = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        fee_type="regular",
    )
    registration.sessions.add(program_session)

    sheets = get_registration_sheets(t_event)
    program_sheet = next((df for df, name in sheets if name == f"PROGRAM - {program_session.title}"), None)

    assert program_sheet is not None
    rows = program_sheet.to_dicts()
    assert any(r["uuid"] == str(registration.uuid) for r in rows)


def test_registration_excel_skips_empty_program_sessions(t_event) -> None:
    """A ``selectable_in_form`` program session with no registrants is omitted from the export."""
    SessionFactory(
        event=t_event,
        title="Empty workshop",
        is_social_event=False,
        is_private=False,
        extra_data={"selectable_in_form": True},
    )

    sheets = get_registration_sheets(t_event)
    assert not any(name.startswith("PROGRAM -") for _, name in sheets)


def test_registration_excel_program_session_selection_flag_shows_all(t_event) -> None:
    """``program_session_selection=True`` exports all non-private non-social sessions."""
    t_event.registration_config = {"program_session_selection": True}
    t_event.save()

    session = SessionFactory(
        event=t_event,
        title="Any program session",
        is_social_event=False,
        is_private=False,
        extra_data={},
    )
    registration = RegistrationFactory(
        event=t_event,
        user=UserFactory(),
        is_accepted=True,
        fee_type="regular",
    )
    registration.sessions.add(session)

    sheets = get_registration_sheets(t_event)
    program_sheet = next((df for df, name in sheets if name == f"PROGRAM - {session.title}"), None)

    assert program_sheet is not None


@pytest.mark.site
class TestEventExcelExport:
    """The Excel export view serves known file codes and rejects unknown ones."""

    @pytest.fixture(autouse=True)
    def setup(self, client, t_event_manager) -> None:
        client.force_login(user=t_event_manager)

    def test_unknown_file_code_is_not_found(self, client, t_event) -> None:
        """An unknown export file code is a 404, not a server error."""
        response = client.get(reverse("event:event_excel", args=[t_event.code, "unknown"]))

        assert response.status_code == status.NOT_FOUND

    def test_known_file_code_returns_the_workbook(self, client, t_event) -> None:
        """A known export file code still returns the generated workbook."""
        response = client.get(reverse("event:event_excel", args=[t_event.code, "registrations"]))

        assert response.status_code == status.OK
        assert response["Content-Type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8"
        )
        assert response["Content-Disposition"] == (f'attachment; filename="{t_event.code}_registrations.xlsx"')
        assert response.content.startswith(b"PK")

    def test_failing_sheet_builder_is_a_server_error(self, client, t_event, monkeypatch) -> None:
        """A genuine failure while building the workbook is not masked as a 404."""

        def broken_builder(event: Any) -> NoReturn:
            raise RuntimeError("broken builder")

        monkeypatch.setattr("evan.site.views.events.get_registration_sheets", broken_builder)
        client.raise_request_exception = False

        response = client.get(reverse("event:event_excel", args=[t_event.code, "registrations"]))

        assert response.status_code == status.INTERNAL_SERVER_ERROR
