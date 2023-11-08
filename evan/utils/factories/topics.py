import factory


class TopicFactory(factory.django.DjangoModelFactory):
    """Factory for Topic model."""

    name = factory.Faker("text")

    class Meta:  # noqa: D106
        model = "evan.Topic"
