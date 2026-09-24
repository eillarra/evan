from datetime import UTC, timedelta

import factory
from factory.declarations import LazyAttribute, Sequence

# Existing events are all-modules-on and listed (see the 0028 backfill migration);
# tests for minimal/new events override these explicitly.
ALL_MODULES_ON = {
    "payments": True,
    "content": True,
    "program": True,
    "papers": True,
    "communications": True,
}


class EventFactory(factory.django.DjangoModelFactory):
    """Factory for Event model."""

    class Meta:  # noqa: D106
        model = "evan.Event"

    code = Sequence(lambda n: f"event-{n}")
    name = Sequence(lambda n: f"Event {n}")
    start_date = factory.Faker("date_time_between", start_date="+2d", end_date="+7d", tzinfo=UTC)  # type: ignore
    end_date = factory.Faker("date_time_between", start_date="+20d", end_date="+24d", tzinfo=UTC)  # type: ignore
    registration_start_date = LazyAttribute(lambda o: o.end_date - timedelta(days=10))
    registration_deadline = LazyAttribute(lambda o: o.end_date - timedelta(days=5))
    listing_status = "listed"
    config = factory.LazyAttribute(lambda o: {"modules": dict(ALL_MODULES_ON)})
