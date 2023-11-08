import factory


class RegistrationFactory(factory.django.DjangoModelFactory):
    """Factory for Registration model."""

    class Meta:  # noqa: D106
        model = "evan.Registration"
