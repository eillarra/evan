from datetime import UTC, timedelta

import factory
from factory.declarations import LazyAttribute, Sequence
from factory.faker import Faker


class EventFactory(factory.django.DjangoModelFactory):
    """Factory for Event model."""

    class Meta:  # noqa: D106
        model = "evan.Event"

    code = Sequence(lambda n: f"event-{n}")
    name = Sequence(lambda n: f"Event {n}")
    start_date = Faker("date_time_this_month", tzinfo=UTC)
    end_date = LazyAttribute(lambda o: o.start_date + timedelta(days=3))
    registration_start_date = LazyAttribute(lambda o: o.start_date - timedelta(days=30))
    registration_deadline = LazyAttribute(lambda o: o.start_date - timedelta(days=1))
