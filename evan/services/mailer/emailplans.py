"""Recipient resolution, rendering, and execution logic for EmailPlans.

The filter spec lives on :class:`evan.models.emails.EmailPlan.filters` as a JSON
field with this shape::

    {
      "fee_types": ["member", "student"],
      "sessions": {"ids": [1, 2], "match": "all" | "any"},
      "session_days": ["2025-09-10", "2025-09-11"],
      "payment_status": "paid" | "unpaid" | null,
    }

Every dimension is optional: an empty value means "no filter on this dimension".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import connection
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from evan.services.mailer.base import render_context


if TYPE_CHECKING:
    from evan.models import Registration, Session, User
    from evan.models.emails import EmailPlan


def _get_filters(plan: EmailPlan) -> dict:
    """Return the plan's filter spec as a dict with all dimensions present.

    :param plan: The EmailPlan to read filters from.
    :returns: A dict with keys ``fee_types``, ``sessions``, ``session_days``, ``payment_status``.
    """
    filters = plan.filters or {}
    return {
        "fee_types": filters.get("fee_types") or [],
        "sessions": filters.get("sessions") or {},
        "session_days": filters.get("session_days") or [],
        "payment_status": filters.get("payment_status"),
    }


def logs_for_plan(plan: EmailPlan) -> QuerySet:
    """Return the EmailLog queryset for emails sent by this plan.

    Uses ``tags__contains`` on MySQL and ``tags__icontains`` on SQLite, because
    SQLite does not support the ``contains`` lookup on JSON fields.

    :param plan: The EmailPlan to filter logs for.
    :returns: A queryset of :class:`EmailLog` tagged with ``emailplan.id:<pk>``.
    """
    from evan.models.emails import EmailLog

    tag = f"emailplan.id:{plan.pk}"
    if connection.vendor == "sqlite":
        return EmailLog.objects.filter(tags__icontains=tag)
    return EmailLog.objects.filter(tags__contains=[tag])


def resolve_recipients(plan: EmailPlan) -> QuerySet[Registration]:
    """Resolve the filter spec to a queryset of matching registrations.

    The base queryset is always ``event.registrations`` restricted to accepted
    registrations (``is_accepted=True``), with ``select_related("user")`` to
    avoid N+1 when accessing the recipient user. Pending (``is_accepted=None``)
    and rejected (``is_accepted=False``) registrations are excluded.

    :param plan: The EmailPlan to resolve recipients for.
    :returns: A queryset of :class:`Registration` instances matching all active filters.
    """
    filters = _get_filters(plan)
    queryset = plan.event.registrations.filter(is_accepted=True).select_related("user")

    fee_types = filters["fee_types"]
    if fee_types:
        queryset = queryset.filter(fee_type__in=fee_types)

    sessions_spec = filters["sessions"]
    session_ids = sessions_spec.get("ids") or []
    session_match = sessions_spec.get("match", "any")
    if session_ids:
        if session_match == "all":
            # Registrations registered for ALL listed sessions: annotate the count
            # of matching sessions and require it to equal the number requested.
            queryset = (
                queryset.filter(sessions__id__in=session_ids)
                .annotate(matched_session_count=Count("sessions", filter=Q(sessions__id__in=session_ids)))
                .filter(matched_session_count=len(session_ids))
            )
        else:
            # "any": registered for at least one of the listed sessions.
            queryset = queryset.filter(sessions__id__in=session_ids).distinct()

    session_days = filters["session_days"]
    if session_days:
        queryset = queryset.filter(sessions__start_at__date__in=session_days).distinct()

    payment_status = filters["payment_status"]
    if payment_status == "paid":
        queryset = queryset.filter(saldo__gte=0)
    elif payment_status == "unpaid":
        queryset = queryset.filter(saldo__lt=0)

    return queryset


def resolve_recipients_count(event, filters: dict) -> int:
    """Return the number of registrations matching a filter spec on an event.

    Unlike :func:`resolve_recipients` this does not require a saved
    :class:`EmailPlan`; it accepts the filter dict directly, which is useful
    for the ``recipients_count`` API action called from the form before a
    plan is saved.

    :param event: The event whose registrations are filtered.
    :param filters: A filter spec dict with optional ``fee_types``, ``sessions``,
        ``session_days``, and ``payment_status`` keys.
    :returns: The number of accepted registrations matching the filters.
    """
    from evan.models import EmailPlan

    plan = EmailPlan(event=event, filters=filters or {})
    return resolve_recipients(plan).count()


def get_random_registration(plan: EmailPlan) -> Registration | None:
    """Pick a random registration matching the filter spec, for preview rendering.

    :param plan: The EmailPlan to find a preview registration for.
    :returns: A random matching :class:`Registration`, or None when none match.
    """
    return resolve_recipients(plan).order_by("?").first()


def _get_template_context(plan: EmailPlan, registration: Registration) -> dict:
    """Build the template rendering context for a registration.

    ``session`` is the first matched session when the plan filters by sessions,
    otherwise ``None``.

    :param plan: The EmailPlan being rendered.
    :param registration: The registration to render for.
    :returns: A context dict with ``event``, ``user``, and ``session`` keys.
    """
    sessions_spec = _get_filters(plan)["sessions"]
    session_ids = sessions_spec.get("ids") or []
    session: Session | None = None
    if session_ids:
        session = registration.sessions.filter(id__in=session_ids).order_by("start_at").first()

    return {
        "event": plan.event,
        "user": registration.user,
        "session": session,
    }


def render_for_registration(plan: EmailPlan, registration: Registration) -> tuple[str, str]:
    """Render the plan's subject and body for a single registration.

    :param plan: The EmailPlan to render.
    :param registration: The registration to render against.
    :returns: A tuple of (rendered_subject, rendered_body).
    """
    context = _get_template_context(plan, registration)
    subject = render_context(plan.subject, context)
    body = render_context(plan.body, context)
    return subject, body


def execute_plan(plan: EmailPlan) -> int:
    """Resolve recipients and create one ``EmailLog`` per recipient, then mark the plan sent.

    The plan is claimed atomically: ``sent_at`` is set via an ``update()`` filtered
    by ``sent_at__isnull=True``. If zero rows are affected (another worker already
    claimed it), the function returns 0 without creating any logs.

    :param plan: The EmailPlan to execute.
    :returns: The number of EmailLog entries created.
    """
    from evan.models.emails import EmailLog, EmailPlan

    # Atomic claim: only proceed if this worker sets sent_at from NULL to now.
    claimed = EmailPlan.objects.filter(pk=plan.pk, sent_at__isnull=True).update(sent_at=timezone.now())
    if not claimed:
        return 0

    recipients = list(resolve_recipients(plan))
    if not recipients:
        return 0

    base_tags = [f"emailplan.id:{plan.pk}", "type:emailplan", f"event.id:{plan.event_id}"]
    logs: list[EmailLog] = []
    for registration in recipients:
        user: User = registration.user
        subject, body = render_for_registration(plan, registration)
        logs.append(
            EmailLog(
                event=plan.event,
                from_email=plan.from_email,
                to=[user.email],
                bcc=plan.bcc,
                reply_to=plan.reply_to,
                subject=subject,
                body=body,
                tags=base_tags + [f"user.id:{user.pk}"],
            )
        )

    chunk_size = 500
    created = 0
    for offset in range(0, len(logs), chunk_size):
        chunk = logs[offset : offset + chunk_size]
        EmailLog.objects.bulk_create(chunk)
        created += len(chunk)

    return created
