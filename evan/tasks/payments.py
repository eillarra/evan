from datetime import timedelta

import sentry_sdk
from django.utils.timezone import now
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from evan.models.payments import RegistrationPaymentAttempt


STALE_PENDING_ATTEMPT_THRESHOLD = timedelta(hours=2)


@db_periodic_task(crontab(hour="*/4", minute=0))
def alert_on_stale_payment_attempts() -> None:
    """Surface payment attempts stuck in PENDING beyond a normal payment session's lifetime.

    A registration whose Worldline feedback (browser redirect or server-to-server
    callback) never arrived stays PENDING with a burned ORDERID, blocking retries
    until an admin manually regenerates the payment hash. Without this alert, such
    cases are only discovered when the affected user complains.
    """
    stale_attempts = list(
        RegistrationPaymentAttempt.objects.filter(
            status=RegistrationPaymentAttempt.PENDING,
            created_at__lt=now() - STALE_PENDING_ATTEMPT_THRESHOLD,
        )
        .select_related("registration", "registration__event")
        .order_by("created_at")
    )
    if not stale_attempts:
        return

    registration_ids = [attempt.registration_id for attempt in stale_attempts]
    # Per-attempt diagnostic attached as extra data so each Sentry event shows
    # whether the stuck attempt is a "no callback ever delivered" case (empty
    # callback_data) or a "callback arrived but status not finalised" case
    # (EXCEPTION 52/92 left pending by design). Keeps the message string stable
    # so Sentry keeps grouping all occurrences under one issue.
    diagnostic = [
        {
            "registration_id": attempt.registration_id,
            "order_id": attempt.order_id,
            "age_hours": round((now() - attempt.created_at).total_seconds() / 3600, 1),
            "callback_received": bool(attempt.callback_data),
            "last_status": (attempt.callback_data or {}).get("STATUS"),
            "event_id": attempt.registration.event_id,
            "event_name": attempt.registration.event.name,
        }
        for attempt in stale_attempts
    ]
    count = len(stale_attempts)
    sentry_sdk.capture_message(
        f"{count} Worldline payment attempt(s) stuck in PENDING over "
        f"{STALE_PENDING_ATTEMPT_THRESHOLD}: registration ids {registration_ids}",
        level="warning",
        extras={"stale_attempts": diagnostic},
    )
