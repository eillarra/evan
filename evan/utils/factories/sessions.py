from datetime import UTC, timedelta

import factory
from factory.declarations import LazyAttribute, SubFactory
from factory.faker import Faker

from .events import EventFactory


def generate_session_start_time(obj):
    """Generate a start time within the event's date range."""
    if obj.event:
        fake = Faker._get_faker()
        return fake.date_time_between(start_date=obj.event.start_date, end_date=obj.event.end_date, tzinfo=UTC)
    return None


class SessionFactory(factory.django.DjangoModelFactory):
    """Factory for Session model."""

    event = SubFactory(EventFactory)
    title = Faker("sentence", nb_words=4)  # Shorter title to avoid max length issues
    description = Faker("text")
    start_at = LazyAttribute(generate_session_start_time)
    end_at = LazyAttribute(lambda o: o.start_at + timedelta(hours=2) if o.start_at else None)

    class Meta:  # noqa: D106
        model = "evan.Session"
