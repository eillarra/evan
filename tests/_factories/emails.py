import factory
from factory.declarations import SubFactory
from factory.faker import Faker

from evan.models import EmailTemplate


class EmailTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmailTemplate

    code = Faker("word")
    from_email = "test@example.com"
    bcc_email = ""
    reply_to_email = ""
    subject = "Test Subject"
    body = "Test Body"
    action_name = "Test Action"
    position = 0


class EmailLogFactory(factory.django.DjangoModelFactory):
    """Factory for EmailLog model."""

    class Meta:
        model = "evan.EmailLog"

    from_email = "sender@example.com"
    to = ["recipient@example.com"]
    bcc = []
    reply_to = []
    subject = "Test subject"
    body = "Test **markdown** body"
    event = SubFactory("tests._factories.events.EventFactory")
