import factory


class ContentFactory(factory.django.DjangoModelFactory):
    """Factory for Content model."""

    key = factory.Sequence(lambda n: f"key.{n}")
    value = factory.Faker("text")

    class Meta:  # noqa: D106
        model = "evan.Content"
