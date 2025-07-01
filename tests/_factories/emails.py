import factory
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
