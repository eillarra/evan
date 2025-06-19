import factory
from factory.declarations import SubFactory
from factory.django import DjangoModelFactory

from evan.models import Subsession

from .sessions import SessionFactory


class SubsessionFactory(DjangoModelFactory):
    class Meta:
        model = Subsession

    session = SubFactory(SessionFactory)
    title = factory.Sequence(lambda n: f"Subsession {n}")
    order = factory.Sequence(lambda n: n)
