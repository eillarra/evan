from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template import Context, Template


if TYPE_CHECKING:
    from evan.models import EmailTemplate, Event, User


def render_context(body: str, context: dict) -> str:
    """Render a body with a context.

    :param body: The body to render.
    :param context: The context to render the body with.
    :returns: The rendered body.
    """
    templ = Template(body)
    return templ.render(Context(context))


def get_template(event: "Event", code: str, language: str = "nl") -> "EmailTemplate":
    """Get an email template for an education.

    :param education: The education to get the email template for.
    :param code: The code of the email template to get.
    :param language: The language of the email template to get.
    :returns: The email template for the education, code and language.
    :raises ValueError: If the email template is not found.
    """
    from evan.models import EmailTemplate

    try:
        return EmailTemplate.objects.get(code=code, event=event, language=language)
    except EmailTemplate.DoesNotExist:
        try:
            return EmailTemplate.objects.get(code=code, education=None, language=language)
        except EmailTemplate.DoesNotExist:
            send_email_to_admins(f"Email template not found for {event} EOM", f"{code} - {language}")

    raise ValueError(f"Email template not found for {event} - {code} - {language}")


def send_email_to_admins(subject: str, message: str = "") -> None:
    """Send an email to the admins.

    :param subject: The subject of the email.
    :param message: The message of the email.
    """
    django_send_mail(
        subject if subject.startswith("[evan] ") else f"[evan] {subject}",
        message,
        "UGent <evan@ugent.be>",
        settings.ADMINS,
        fail_silently=False,
    )


def schedule_email(
    *,
    from_email: str = "UGent <evan@ugent.be>",
    to: list[str],
    subject: str,
    text_content: str,
    bcc: list[str] | None = None,
    reply_to: list[str] | None = None,
    log_user: Optional["User"] = None,
    log_event: Optional["Event"] = None,
    tags: list[str] | None = None,
) -> None:
    """Schedule an email to be sent.

    :param from_email: The email address to send the email from.
    :param to: The email addresses to send the email to.
    :param subject: The subject of the email.
    :param text_content: The text content of the email.
    :param bcc: The email addresses to send the email bcc to.
    :param reply_to: The email addresses to set as reply-to.
    :param log_user: The user to log the email for.
    :param log_event: The event to log the email for.
    :param tags: The tags to log the email with.
    """
    from evan.models.emails import EmailLog

    tags = tags or []

    if log_user and f"user.id:{log_user.pk}" not in tags:
        tags.append(f"user.id:{log_user.pk}")

    if log_event and f"event.id:{log_event.pk}" not in tags:
        tags.append(f"event.id:{log_event.pk}")

    # Remove duplicate entries
    unique_to = list(set(to))
    unique_bcc = list(set(bcc or []))
    unique_tags = list(set(tags))

    EmailLog.objects.create(
        from_email=from_email,
        to=unique_to,
        bcc=unique_bcc,
        reply_to=reply_to or [],
        subject=subject,
        body=text_content,
        event=log_event,
        tags=unique_tags,
    )


def schedule_template_email(
    *,
    template: "EmailTemplate",
    to: list[str],
    bcc: list[str] | None = None,
    reply_to: list[str] | None = None,
    context: dict | None = None,
    log_user: Optional["User"] = None,
    log_event: Optional["Event"] = None,
    tags: list[str] | None = None,
) -> None:
    """Schedule an email based on a template.

    :param template: The email template to use.
    :param to: The email addresses to send the email to.
    :param bcc: The email addresses to send the email bcc to.
    :param reply_to: The email addresses to set as reply-to.
    :param context: The context to render the email with.
    :param log_user: The user to log the email for.
    :param log_event: The event to log the email for.
    :param tags: The tags to log the email with.
    """
    try:
        evan_email = "UGent <evan@ugent.be>"
        reply_to = reply_to or template.reply_to or [evan_email]

        schedule_email(
            from_email=template.from_email or evan_email,
            to=to,
            subject=render_context(template.subject, context or {}),
            text_content=render_context(template.body, context or {}),
            bcc=template.bcc + (bcc or []),
            reply_to=reply_to,
            log_user=log_user,
            log_event=log_event,
            tags=tags,
        )

    except Exception as exc:
        send_email_to_admins("Email error", f"Error while sending email: {exc}")
        raise exc
