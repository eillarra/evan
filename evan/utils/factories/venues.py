import factory
from factory.declarations import Sequence, SubFactory
from factory.faker import Faker


class VenueFactory(factory.django.DjangoModelFactory):
    """Factory for Venue model."""

    class Meta:  # noqa: D106
        model = "evan.Venue"

    event = SubFactory("evan.utils.factories.events.EventFactory")
    name = Faker("company")
    city = Faker("city")
    is_main = False
    presentation = Faker("text", max_nb_chars=200)
    website = Faker("url")
    google_place_id = Faker("uuid4")


class RoomFactory(factory.django.DjangoModelFactory):
    """Factory for Room model."""

    class Meta:  # noqa: D106
        model = "evan.Room"

    venue = SubFactory(VenueFactory)
    name = Faker("word")
    max_capacity = Faker("pyint", min_value=10, max_value=500)
    position = Sequence(lambda n: n)
