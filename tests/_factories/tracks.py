import factory
from factory.faker import Faker


class TrackFactory(factory.django.DjangoModelFactory):
    """Factory for Track model."""

    name = Faker("text", max_nb_chars=128)
    position = Faker("random_int")

    class Meta:  # noqa: D106
        model = "evan.Track"
