from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template import Context, Template


if TYPE_CHECKING:
    from evan.models.emails import EmailTemplate


def render_context(body: str, context: dict) -> str:
    """Render a body with a context.

    :param body: The body to render.
    :param context: The context to render the body with.
    :returns: The rendered body.
    """
    templ = Template(body)
    return templ.render(Context(context))


def send_email_to_admins(subject: str, message: str = "") -> None:
    """Send an email to the admins.

    :param subject: The subject of the email.
    :param message: The message of the email.
    """
    django_send_mail(
        subject if subject.startswith("[Evan] ") else f"[Evan] {subject}",
        message,
        "Evan <evan@ugent.be>",
        settings.ADMINS,
        fail_silently=False,
    )


def schedule_email(
    *,
    from_email: str = "Evan <evan@ugent.be>",
    to: list[str],
    subject: str,
    text_content: str,
    bcc: list[str] | None = None,
    reply_to: list[str] | None = None,
) -> None:
    """Schedule an email to be sent.

    :param from_email: The email address to send the email from.
    :param to: The email addresses to send the email to.
    :param subject: The subject of the email.
    :param text_content: The text content of the email.
    :param bcc: The email addresses to send the email bcc to.
    :param reply_to: The email addresses to set as reply-to.
    """
    from evan.models.emails import EmailLog

    unique_to = list(set(to))
    unique_bcc = list(set(bcc or []))

    EmailLog.objects.create(
        from_email=from_email,
        to=unique_to,
        bcc=unique_bcc,
        reply_to=reply_to or [],
        subject=subject,
        body=text_content,
    )


def schedule_template_email(
    *,
    template: "EmailTemplate",
    to: list[str],
    context: dict | None = None,
) -> None:
    """Schedule an email based on a template.

    :param template: The email template to use.
    :param to: The email addresses to send the email to.
    :param bcc: The email addresses to send the email bcc to.
    :param context: The context to render the email with.
    """
    try:
        schedule_email(
            from_email=template.from_email,
            to=to,
            subject=render_context(template.subject, context or {}),
            text_content=render_context(template.body, context or {}),
            bcc=template.bcc,
            reply_to=template.reply_to,
        )

    except Exception as exc:
        send_email_to_admins("Email error", f"Error while sending email: {exc}")
        raise exc
