import datetime
import os
from smtplib import SMTPRecipientsRefused
from time import sleep

from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import now
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from markdown import markdown

from evan.models.emails import EmailLog
from evan.services.mailer.base import send_email_to_admins


EMAILS_PER_MINUTE = int(os.getenv("UGENT_EMAILS_PER_MINUTE", 2))


@db_periodic_task(crontab(minute="*"))
def send_email() -> None:
    """Send the emails that are scheduled.

    TODO: if we get access to mass mailing, use EMAILS_PER_MINUTE to adjust the amount of emails sent
    """
    emails = EmailLog.objects.filter(sent_at=None).order_by("created_at")[:EMAILS_PER_MINUTE]

    for email in emails:
        try:
            html_content = markdown(email.body)
            msg = EmailMultiAlternatives(
                email.subject,
                email.body,
                from_email=email.from_email,
                to=email.to,
                bcc=email.bcc,
                reply_to=email.reply_to,
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            email.sent_at = now()
            email.save()
        except SMTPRecipientsRefused as e:
            # set sent at as epoch 0 to prevent retrying
            email.sent_at = datetime.datetime.fromtimestamp(0, datetime.UTC)
            email.save()
            send_email_to_admins("Email error", f"Recipient refused: {e}")
            raise e
        except Exception as e:
            send_email_to_admins("Email error", f"Error while sending email: {e}")
            raise e

        sleep(60 / EMAILS_PER_MINUTE)
