import factory
from factory.declarations import SubFactory
from factory.faker import Faker

from .events import EventFactory


class KeynoteFactory(factory.django.DjangoModelFactory):
    """Factory for Keynote model."""

    event = SubFactory(EventFactory)
    code = factory.Sequence(lambda n: f"K{n}")
    title = Faker("sentence", nb_words=4)
    speaker = Faker("name")
    bio = Faker("text")
    abstract = Faker("text")

    class Meta:
        model = "evan.Keynote"
