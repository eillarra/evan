from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from evan.models.registrations import Registration


from .base import schedule_template_email


def schedule_registration_email(registration: "Registration", *, code: str) -> None:
    """Schedule a registration email."""

    schedule_template_email(
        template=registration.event.get_email_template(code=code),  # type: ignore
        to=[registration.user.email],
        context={"registration": registration},
        log_user=registration.user,
        log_event=registration.event,
        tags=[f"registration.id:{registration.pk}", f"type:{code}"],
    )
