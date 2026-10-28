"""Serializer validation for registration extra data.

Accompanying-person social-event selections are normalised once, at the input
boundary, so fees, capacity checks, headcounts and badges all read integers.
"""

from types import SimpleNamespace

import pytest

from evan.api.serializers import AuthRegistrationRetrieveSerializer, RegistrationRetrieveSerializer
from evan.models import Fee
from tests._factories import EventFactory, RegistrationFactory, SessionFactory, UserFactory


@pytest.fixture
def event(db):
    """An event with a regular fee, ready for registration payloads."""
    event = EventFactory()
    Fee.objects.create(event=event, type="regular", value=100)
    return event


def _create_serializer(event, extra_data):
    """Build a create serializer for ``extra_data`` on ``event``."""
    view = SimpleNamespace(kwargs={"code": event.code})
    return RegistrationRetrieveSerializer(
        data={"fee_type": "regular", "extra_data": extra_data},
        context={"view": view},
    )


def _validated_extra_data(event, extra_data):
    """Return the normalised extra data, asserting the payload is valid."""
    serializer = _create_serializer(event, extra_data)
    assert serializer.is_valid(), serializer.errors
    return serializer.validated_data["extra_data"]


def _errors(event, extra_data):
    """Return the validation errors, asserting the payload is invalid."""
    serializer = _create_serializer(event, extra_data)
    assert not serializer.is_valid()
    return serializer.errors


@pytest.mark.api
class TestRegistrationExtraDataSerializer:
    """Accompanying-person social-event IDs are normalised and validated."""

    def test_numeric_string_is_converted_to_int(self, event) -> None:
        social = SessionFactory(event=event, is_social_event=True, extra_attendees_fee=20)

        data = _validated_extra_data(event, {"accompanying_persons": [{"selected_social_events": [str(social.id)]}]})

        assert data["accompanying_persons"][0]["selected_social_events"] == [social.id]

    def test_integer_ids_are_kept(self, event) -> None:
        social = SessionFactory(event=event, is_social_event=True)

        data = _validated_extra_data(event, {"accompanying_persons": [{"selected_social_events": [social.id]}]})

        assert data["accompanying_persons"][0]["selected_social_events"] == [social.id]

    def test_non_numeric_string_is_rejected(self, event) -> None:
        errors = _errors(event, {"accompanying_persons": [{"selected_social_events": ["abc"]}]})

        assert "integer IDs" in str(errors)

    def test_boolean_and_float_are_rejected(self, event) -> None:
        assert "integer IDs" in str(_errors(event, {"accompanying_persons": [{"selected_social_events": [True]}]}))
        assert "integer IDs" in str(_errors(event, {"accompanying_persons": [{"selected_social_events": [1.0]}]}))

    def test_null_selection_is_rejected(self, event) -> None:
        errors = _errors(event, {"accompanying_persons": [{"selected_social_events": None}]})

        assert "must be a list" in str(errors)

    def test_null_persons_list_is_rejected(self, event) -> None:
        errors = _errors(event, {"accompanying_persons": None})

        assert "must be a list" in str(errors)

    def test_non_list_persons_is_rejected(self, event) -> None:
        errors = _errors(event, {"accompanying_persons": {"name": "Jane"}})

        assert "must be a list" in str(errors)

    def test_non_object_person_is_rejected(self, event) -> None:
        errors = _errors(event, {"accompanying_persons": ["Jane"]})

        assert "must be an object" in str(errors)

    def test_non_object_extra_data_is_rejected(self, event) -> None:
        errors = _errors(event, ["not", "an", "object"])

        assert "must be an object" in str(errors)

    def test_object_selection_is_rejected(self, event) -> None:
        errors = _errors(event, {"accompanying_persons": [{"selected_social_events": [{}]}]})

        assert "integer IDs" in str(errors)

    def test_session_from_another_event_is_rejected(self, event) -> None:
        other = SessionFactory(event=EventFactory(), is_social_event=True)

        errors = _errors(event, {"accompanying_persons": [{"selected_social_events": [other.id]}]})

        assert "social events of this event" in str(errors)

    def test_non_social_session_is_rejected(self, event) -> None:
        session = SessionFactory(event=event, is_social_event=False)

        errors = _errors(event, {"accompanying_persons": [{"selected_social_events": [session.id]}]})

        assert "social events of this event" in str(errors)

    def test_empty_persons_list_is_allowed(self, event) -> None:
        data = _validated_extra_data(event, {"accompanying_persons": []})

        assert data["accompanying_persons"] == []

    def test_accompanying_persons_refused_when_event_disallows(self, event) -> None:
        event.registration_config = {"accompanying_persons": False}
        event.save(update_fields=["registration_config"])

        errors = _errors(event, {"accompanying_persons": [{"name": "Jane"}]})

        assert "does not accept accompanying persons" in str(errors)

    def test_missing_selection_is_allowed(self, event) -> None:
        data = _validated_extra_data(event, {"accompanying_persons": [{"name": "Jane"}]})

        assert data["accompanying_persons"] == [{"name": "Jane"}]

    def test_other_extra_data_keys_are_preserved(self, event) -> None:
        social = SessionFactory(event=event, is_social_event=True)

        data = _validated_extra_data(
            event,
            {
                "paper_id": "P-1",
                "accompanying_persons": [{"name": "Jane", "selected_social_events": [social.id]}],
            },
        )

        assert data["paper_id"] == "P-1"
        assert data["accompanying_persons"][0]["name"] == "Jane"


@pytest.mark.api
class TestRegistrationUpdateExtraDataSerializer:
    """Updates resolve the event from the registration, without view context."""

    def test_update_converts_numeric_string(self, event) -> None:
        social = SessionFactory(event=event, is_social_event=True)
        registration = RegistrationFactory(event=event, user=UserFactory(), fee_type="regular")

        serializer = AuthRegistrationRetrieveSerializer(
            registration,
            data={"extra_data": {"accompanying_persons": [{"selected_social_events": [str(social.id)]}]}},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        selections = serializer.validated_data["extra_data"]["accompanying_persons"][0]["selected_social_events"]
        assert selections == [social.id]

    def test_update_rejects_session_from_another_event(self, event) -> None:
        other = SessionFactory(event=EventFactory(), is_social_event=True)
        registration = RegistrationFactory(event=event, user=UserFactory(), fee_type="regular")

        serializer = AuthRegistrationRetrieveSerializer(
            registration,
            data={"extra_data": {"accompanying_persons": [{"selected_social_events": [other.id]}]}},
            partial=True,
        )

        assert not serializer.is_valid()
        assert "social events of this event" in str(serializer.errors)
