from datetime import timedelta

import factory
from factory.declarations import LazyAttribute
from factory.faker import Faker


class SessionFactory(factory.django.DjangoModelFactory):
    """Factory for Session model."""

    title = Faker("text")
    description = Faker("text")
    start_at = Faker("date_time")
    end_at = LazyAttribute(lambda o: o.start_at + timedelta(hours=2))

    class Meta:  # noqa: D106
        model = "evan.Session"
