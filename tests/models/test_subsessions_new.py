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

    def test_subsession_str(self, subsession):
        expected = f"{subsession.session.title} - {subsession.title}"
        assert str(subsession) == expected

    def test_subsession_ordering(self, session):
        sub1 = Subsession.objects.create(session=session, title="Sub 1", order=2)
        sub2 = Subsession.objects.create(session=session, title="Sub 2", order=1)
        sub3 = Subsession.objects.create(session=session, title="Sub 3", order=3)

        subsessions = list(Subsession.objects.filter(session=session))
        assert subsessions[0] == sub2  # order=1
        assert subsessions[1] == sub1  # order=2
        assert subsessions[2] == sub3  # order=3

    def test_subsession_validation_start_before_session(self, subsession):
        # Set session times
        subsession.session.start_at = timezone.now()
        subsession.session.save()

        # Try to set subsession start before session start
        subsession.start_at = subsession.session.start_at - datetime.timedelta(hours=1)

        with pytest.raises(ValidationError):
            subsession.clean()

    def test_subsession_validation_end_after_session(self, subsession):
        # Set session times
        subsession.session.end_at = timezone.now()
        subsession.session.save()

        # Try to set subsession end after session end
        subsession.end_at = subsession.session.end_at + datetime.timedelta(hours=1)

        with pytest.raises(ValidationError):
            subsession.clean()

    def test_subsession_validation_start_after_end(self, subsession):
        subsession.start_at = timezone.now()
        subsession.end_at = subsession.start_at - datetime.timedelta(hours=1)

        with pytest.raises(ValidationError):
            subsession.clean()
