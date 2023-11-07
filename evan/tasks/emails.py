from huey.contrib.djhuey import task

from evan.services.mailer import send_email


@task()  # rate_limit="2/m")
def send_template_email(template: str, subject: str, from_email: str, to: list[str], context_data: dict | None = None):
    send_email(
        template=template,
        subject=subject,
        from_email=from_email,
        to=to,
        context_data=context_data or {},
    )
