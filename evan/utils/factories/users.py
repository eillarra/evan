import factory
from django.utils import timezone


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating a user."""

    class Meta:  # noqa: D106
        model = "evan.User"

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    last_login = factory.LazyFunction(timezone.now)

    username = factory.LazyAttribute(lambda self: self.email.split("@")[0])
    password = factory.django.Password("evan")


class AdminFactory(UserFactory):
    """Factory for creating an admin user."""

    username = "evan"
    first_name = "Evan"
    last_name = "Admin"
    email = "evan@ugent.be"
    is_staff = True
    is_superuser = True
