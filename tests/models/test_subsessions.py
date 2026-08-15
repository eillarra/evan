import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from evan.models import Subsession
from tests._factories import SessionFactory


@pytest.fixture
def session(db, t_event):
    return SessionFactory(event=t_event)


@pytest.fixture
def subsession(db, session):
    return Subsession.objects.create(
        session=session,
        title="Morning Session",
        order=1,
    )


@pytest.mark.django_db
class TestSubsessionModel:
    def test_create_subsession(self, session):
        subsession = Subsession.objects.create(
            session=session,
            title="Test Subsession",
            order=1,
        )
        assert subsession.title == "Test Subsession"
        assert subsession.session == session
        assert subsession.order == 1

    def test_str(self, subsession):
        expected = f"{subsession.session.title} - {subsession.title}"
        assert str(subsession) == expected

    def test_ordering(self, session):
        sub1 = Subsession.objects.create(session=session, title="Sub 1", order=2)
        sub2 = Subsession.objects.create(session=session, title="Sub 2", order=1)
        sub3 = Subsession.objects.create(session=session, title="Sub 3", order=3)

        subsessions = list(Subsession.objects.filter(session=session))
        assert subsessions[0] == sub2
        assert subsessions[1] == sub1
        assert subsessions[2] == sub3

    def test_validation_start_before_session(self, subsession):
        subsession.session.start_at = timezone.now()
        subsession.session.save()
        subsession.start_at = subsession.session.start_at - datetime.timedelta(hours=1)

        with pytest.raises(ValidationError):
            subsession.clean()

    def test_validation_end_after_session(self, subsession):
        subsession.session.end_at = timezone.now()
        subsession.session.save()
        subsession.end_at = subsession.session.end_at + datetime.timedelta(hours=1)

        with pytest.raises(ValidationError):
            subsession.clean()

    def test_validation_start_after_end(self, subsession):
        subsession.start_at = timezone.now()
        subsession.end_at = subsession.start_at - datetime.timedelta(hours=1)

        with pytest.raises(ValidationError):
            subsession.clean()


@pytest.mark.django_db
class TestSubsessionPaperCrossAssignment:
    """A subsession program cannot reference a paper already assigned to another session or subsession."""

    def test_paper_in_different_session_is_rejected(self, t_event, session, subsession) -> None:
        from tests._factories import PaperFactory

        other_session = SessionFactory(event=t_event)
        paper = PaperFactory(event=t_event, session=other_session)

        subsession.program = f"[paper:{paper.id}]"
        with pytest.raises(ValidationError, match="already assigned to session"):
            subsession.clean()

    def test_paper_in_different_subsession_is_rejected(self, t_event, session) -> None:
        from tests._factories import PaperFactory, SubsessionFactory

        first_sub = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=first_sub)
        first_sub.program = f"[paper:{paper.id}]"
        first_sub.save()

        second_sub = SubsessionFactory(session=session)
        second_sub.program = f"[paper:{paper.id}]"
        with pytest.raises(ValidationError, match="already assigned to subsession"):
            second_sub.clean()

    def test_paper_in_same_subsession_passes(self, t_event, session) -> None:
        from tests._factories import PaperFactory, SubsessionFactory

        sub = SubsessionFactory(session=session)
        paper = PaperFactory(event=t_event, session=session, subsession=sub)
        sub.program = f"[paper:{paper.id}]"
        sub.clean()  # no ValidationError raised

    def test_nonexistent_paper_id_is_rejected(self, t_event, subsession) -> None:
        subsession.program = "[paper:999999]"
        with pytest.raises(ValidationError):
            subsession.clean()


@pytest.mark.django_db
class TestSubsessionKeynoteCrossAssignment:
    """A subsession program cannot reference a keynote already assigned to another session or subsession."""

    def test_keynote_in_different_session_is_rejected(self, t_event, session, subsession) -> None:
        from tests._factories import KeynoteFactory

        other_session = SessionFactory(event=t_event)
        keynote = KeynoteFactory(event=t_event, session=other_session)

        subsession.program = f"[keynote:{keynote.code}]"
        with pytest.raises(ValidationError, match="already assigned to session"):
            subsession.clean()

    def test_keynote_in_different_subsession_is_rejected(self, t_event, session) -> None:
        from tests._factories import KeynoteFactory, SubsessionFactory

        first_sub = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=first_sub)
        first_sub.program = f"[keynote:{keynote.code}]"
        first_sub.save()

        second_sub = SubsessionFactory(session=session)
        second_sub.program = f"[keynote:{keynote.code}]"
        with pytest.raises(ValidationError, match="already assigned to subsession"):
            second_sub.clean()

    def test_keynote_in_same_subsession_passes(self, t_event, session) -> None:
        from tests._factories import KeynoteFactory, SubsessionFactory

        sub = SubsessionFactory(session=session)
        keynote = KeynoteFactory(event=t_event, session=session, subsession=sub)
        sub.program = f"[keynote:{keynote.code}]"
        sub.clean()  # no ValidationError raised

    def test_nonexistent_keynote_code_is_rejected(self, t_event, subsession) -> None:
        subsession.program = "[keynote:NOPE]"
        with pytest.raises(ValidationError):
            subsession.clean()
