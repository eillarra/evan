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
    stale_attempts = RegistrationPaymentAttempt.objects.filter(
        status=RegistrationPaymentAttempt.PENDING,
        created_at__lt=now() - STALE_PENDING_ATTEMPT_THRESHOLD,
    )
    count = stale_attempts.count()
    if not count:
        return

    registration_ids = list(stale_attempts.values_list("registration_id", flat=True))
    sentry_sdk.capture_message(
        f"{count} Worldline payment attempt(s) stuck in PENDING for over {STALE_PENDING_ATTEMPT_THRESHOLD}: "
        f"registration ids {registration_ids}",
        level="warning",
    )
