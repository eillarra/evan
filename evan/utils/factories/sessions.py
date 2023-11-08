from datetime import timedelta

import factory


class SessionFactory(factory.django.DjangoModelFactory):
    """Factory for Session model."""

    title = factory.Faker("text")
    description = factory.Faker("text")
    start_at = factory.Faker("date_time")
    end_at = factory.LazyAttribute(lambda o: o.start_at + timedelta(hours=2))

    class Meta:  # noqa: D106
        model = "evan.Session"
