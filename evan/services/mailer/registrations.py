import os
from typing import TYPE_CHECKING

from .base import schedule_template_email


if TYPE_CHECKING:
    from evan.models.registrations import Registration


def schedule_registration_email(registration: "Registration", *, code: str) -> None:
    """Schedule a registration email."""

    template = registration.event.get_email_template(code=code)

    if template is None and os.environ.get("DJANGO_SETTINGS_MODULE") == "evan.settings.test":
        return

    schedule_template_email(
        template=template,
        to=[registration.user.email],
        context={"registration": registration},
        log_user=registration.user,
        log_event=registration.event,
        tags=[f"registration.id:{registration.pk}", f"type:{code}"],
    )
