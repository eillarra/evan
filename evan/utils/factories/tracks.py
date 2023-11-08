import factory


class TrackFactory(factory.django.DjangoModelFactory):
    """Factory for Track model."""

    name = factory.Faker("text")
    position = factory.Faker("random_int")

    class Meta:  # noqa: D106
        model = "evan.Track"
