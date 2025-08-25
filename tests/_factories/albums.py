import factory
from factory.declarations import Sequence, SubFactory


class AlbumFactory(factory.django.DjangoModelFactory):
    """Factory for Album model."""

    title = Sequence(lambda n: f"Album {n}")
    event = SubFactory("tests._factories.events.EventFactory")

    class Meta:  # noqa: D106
        model = "evan.Album"
