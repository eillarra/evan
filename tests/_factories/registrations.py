import factory


class RegistrationFactory(factory.django.DjangoModelFactory):
    """Factory for Registration model."""

    fee_type = "regular"

    class Meta:  # noqa: D106
        model = "evan.Registration"
