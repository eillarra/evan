import factory
from factory.faker import Faker


class PaperFactory(factory.django.DjangoModelFactory):
    """Factory for Paper model."""

    title = Faker("text")
    abstract = Faker("text")

    class Meta:  # noqa: D106
        model = "evan.Paper"
