import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from evan.models import Keynote
from tests._factories import EventFactory, KeynoteFactory, SessionFactory, SubsessionFactory, TopicFactory


@pytest.mark.django_db
class TestKeynoteModel:
    def test_str_representation(self):
        keynote = KeynoteFactory(code="K1", title="Test Keynote")
        assert str(keynote) == "K1: Test Keynote"

    def test_unique_code_per_event(self):
        event = EventFactory()
        KeynoteFactory(event=event, code="K1")

        with pytest.raises(IntegrityError):
            KeynoteFactory(event=event, code="K1")

    def test_same_code_different_events(self):
        event1 = EventFactory()
        event2 = EventFactory()

        keynote1 = KeynoteFactory(event=event1, code="K1")
        keynote2 = KeynoteFactory(event=event2, code="K1")

        assert keynote1.code == keynote2.code
        assert keynote1.event != keynote2.event

    def test_extra_data_validation(self):
        keynote = KeynoteFactory()
        keynote.extra_data = {
            "speaker_affiliation": "MIT",
            "speaker_website": "https://speaker.example.com",
            "presentation_url": "https://example.com/slides",
        }
        keynote.save()  # Should not raise

    def test_invalid_extra_data(self):
        keynote = KeynoteFactory()
        keynote.extra_data = {"invalid_field": "value"}  # Will be ignored due to extra="ignore"
        keynote.save()  # Should not raise

    def test_ordering(self):
        event = EventFactory()
        keynote_b = KeynoteFactory(event=event, code="KB")
        keynote_a = KeynoteFactory(event=event, code="KA")
        keynote_c = KeynoteFactory(event=event, code="KC")

        keynotes = list(Keynote.objects.filter(event=event))
        assert keynotes[0] == keynote_a
        assert keynotes[1] == keynote_b
        assert keynotes[2] == keynote_c

    def test_secret_property(self):
        keynote = KeynoteFactory()
        secret = keynote.secret
        assert isinstance(secret, str)
        assert len(secret) == 64  # SHA256 hex digest length

    def test_urls(self):
        keynote = KeynoteFactory()

        api_url = keynote.get_api_url()
        assert api_url.startswith("/api/v1/")
        assert str(keynote.pk) in api_url

        secret_url = keynote.get_secret_url()
        assert isinstance(secret_url, str)
        assert str(keynote.uuid) in secret_url

    def test_keynote_with_session(self):
        session = SessionFactory()
        keynote = KeynoteFactory(event=session.event, session=session)

        assert keynote.session == session

    def test_keynote_with_subsession(self):
        session = SessionFactory()
        subsession = SubsessionFactory(session=session)

        keynote = KeynoteFactory(event=session.event, session=session, subsession=subsession)

        assert keynote.session == session
        assert keynote.subsession == subsession

    def test_keynote_validation_subsession_session_mismatch(self):
        session1 = SessionFactory()
        session2 = SessionFactory(event=session1.event)
        subsession = SubsessionFactory(session=session1)

        keynote = KeynoteFactory.build(event=session1.event, session=session2, subsession=subsession)

        with pytest.raises(ValidationError) as exc_info:
            keynote.clean()

        assert "Subsession must belong to the selected session" in str(exc_info.value)

    def test_keynote_validation_session_event_mismatch(self):
        event1 = EventFactory()
        event2 = EventFactory()
        session = SessionFactory(event=event2)

        keynote = KeynoteFactory.build(event=event1, session=session)

        with pytest.raises(ValidationError) as exc_info:
            keynote.clean()

        assert "Session must belong to the same event" in str(exc_info.value)

    def test_keynote_with_topics(self):
        event = EventFactory()
        topic1 = TopicFactory(event=event)
        topic2 = TopicFactory(event=event)

        keynote = KeynoteFactory(event=event)
        keynote.topics.add(topic1, topic2)

        assert keynote.topics.count() == 2
        assert topic1 in keynote.topics.all()
        assert topic2 in keynote.topics.all()
