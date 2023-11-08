from datetime import UTC, timedelta

import factory


class EventFactory(factory.django.DjangoModelFactory):
    """Factory for Event model."""

    class Meta:  # noqa: D106
        model = "evan.Event"

    code = factory.Sequence(lambda n: f"event-{n}")
    name = factory.Sequence(lambda n: f"Event {n}")
    start_date = factory.Faker("date_time_this_month", tzinfo=UTC)
    end_date = factory.LazyAttribute(lambda o: o.start_date + timedelta(days=3))
    registration_start_date = factory.LazyAttribute(lambda o: o.start_date - timedelta(days=30))
    registration_deadline = factory.LazyAttribute(lambda o: o.start_date - timedelta(days=1))
