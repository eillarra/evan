from celery.decorators import task
from typing import List

from evan.tools.mailer import send_email


@task()
def send_template_email(template: str, subject: str, from_email: str, to: List[str], context_data: dict = {}):
    send_email(template=template, subject=subject, from_email=from_email, to=to, context_data=context_data)
