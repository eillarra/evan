"""Listing moderation: the gate between event creation and public visibility.

Every new event enters ``pending_review``; the platform team lists or declines
it, and organizers are notified of the decision. Organizer edits on an unlisted
event return it to ``pending_review`` and re-notify the team, so a declined
event is never left stuck.
"""

from django.utils import timezone

from evan.models import Event, Permission
from evan.services.mailer.base import schedule_email


PLATFORM_TEAM_EMAIL = "evan@ugent.be"


def organizer_emails(event: Event) -> list[str]:
    """Return the email addresses of the event's organizers (ADMIN+ on the ACL).

    :param event: The event whose organizers are collected.
    :returns: A list of organizer email addresses.
    """
    return list(event.acl.filter(level__gte=Permission.ADMIN).values_list("user__email", flat=True))


def notify_team_of_pending_review(event: Event, *, edited: bool = False) -> None:
    """Notify the platform team that an event awaits (or re-await) listing review.

    :param event: The event awaiting review.
    :param edited: True when the notification follows an organizer edit of an unlisted event.
    """
    action = "was edited and awaits review again" if edited else "was created and awaits review"
    schedule_email(
        to=[PLATFORM_TEAM_EMAIL],
        subject=f"[evan] Event '{event.name}' awaits listing review",
        text_content=(
            f"Event '{event.name}' ({event.full_name}, code '{event.code}') {action}.\n\n"
            f"Public page: {event.get_absolute_url()}\n"
            f"Admin: /admin/evan/event/{event.pk}/change/\n"
        ),
        tags=["type:listing", f"event.id:{event.pk}"],
    )


def notify_organizers_of_decision(event: Event) -> None:
    """Notify an event's organizers of the platform team's listing decision.

    Declined events include the recorded reason.

    :param event: The event whose listing decision was recorded.
    """
    recipients = organizer_emails(event)

    if not recipients:
        return

    if event.listing_status == Event.ListingStatus.LISTED:
        subject = f"[evan] Your event '{event.name}' is now publicly listed"
        body = (
            f"Good news: '{event.name}' has been listed and is now publicly visible.\n\n"
            f"Public page: {event.get_absolute_url()}\n"
            f"Manage: {event.get_manage_url()}\n"
        )
    else:
        subject = f"[evan] Your event '{event.name}' was declined for public listing"
        body = (
            f"'{event.name}' was declined for public listing.\n\n"
            f"Reason: {event.decline_reason or '-'}\n\n"
            "You can edit the event; it will then return to review automatically.\n"
            f"Manage: {event.get_manage_url()}\n"
        )

    schedule_email(
        to=recipients,
        subject=subject,
        text_content=body,
        tags=["type:listing", f"event.id:{event.pk}"],
    )


def record_listing_decision(event: Event, *, decided_by, decision: str, reason: str = "") -> None:
    """Record a platform-team listing decision and notify the organizers.

    :param event: The event being decided on.
    :param decided_by: The staff user who made the decision.
    :param decision: The new listing status (listed or declined).
    :param reason: The decline reason, required for declined events.
    """
    event.listing_status = decision
    event.listing_decided_by = decided_by
    event.listing_decided_at = timezone.now()

    if decision == Event.ListingStatus.DECLINED:
        event.decline_reason = reason

    event.save()
    notify_organizers_of_decision(event)


def return_declined_event_to_review(event: Event) -> None:
    """Return a declined event to pending review after an organizer edit.

    :param event: The event being returned to review.
    """
    event.listing_status = Event.ListingStatus.PENDING_REVIEW
    event.save()
    notify_team_of_pending_review(event, edited=True)
