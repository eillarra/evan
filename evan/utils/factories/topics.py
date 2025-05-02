import factory
from factory.faker import Faker


class TopicFactory(factory.django.DjangoModelFactory):
    """Factory for Topic model."""

    name = Faker("text")

    class Meta:  # noqa: D106
        model = "evan.Topic"
