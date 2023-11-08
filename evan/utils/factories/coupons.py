import factory


class CouponFactory(factory.django.DjangoModelFactory):
    """Factory for Coupon model."""

    notes = factory.Faker("text")

    class Meta:  # noqa: D106
        model = "evan.Coupon"
