import factory
from factory.faker import Faker


class TrackFactory(factory.django.DjangoModelFactory):
    """Factory for Track model."""

    name = Faker("text")
    position = Faker("random_int")

    class Meta:  # noqa: D106
        model = "evan.Track"
