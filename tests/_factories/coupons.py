import factory
from factory.faker import Faker


class CouponFactory(factory.django.DjangoModelFactory):
    """Factory for Coupon model."""

    notes = Faker("text", max_nb_chars=190)

    class Meta:  # noqa: D106
        model = "evan.Coupon"
