from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from typing import List


def send_email(
    *, from_email: str = "Evan <evan@ugent.be>", to: List[str], subject: str, template: str, context_data: dict
):
    text_content = render_to_string(template, context_data)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.send()
