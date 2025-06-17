import factory
from factory.declarations import SelfAttribute, SubFactory
from factory.faker import Faker

from .events import EventFactory
from .sessions import SessionFactory


class PaperFactory(factory.django.DjangoModelFactory):
    """Factory for Paper model."""

    event = SubFactory(EventFactory)
    session = SubFactory(SessionFactory, event=SelfAttribute("..event"))
    title = Faker("sentence", nb_words=4)
    abstract = Faker("text")

    class Meta:  # noqa: D106
        model = "evan.Paper"
