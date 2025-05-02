import factory
from factory.declarations import Sequence
from factory.faker import Faker


class ContentFactory(factory.django.DjangoModelFactory):
    """Factory for Content model."""

    key = Sequence(lambda n: f"key.{n}")
    value = Faker("text")

    class Meta:  # noqa: D106
        model = "evan.Content"
