"""Behaviour tests for the EmailPlan service: recipient resolution, rendering, execution.

We assert outcomes — which registrations match a filter, how many logs are created,
whether the plan is marked sent — not the internal queryset mechanics.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from evan.models import Fee
from evan.services.mailer.emailplans import (
    execute_plan,
    get_random_registration,
    logs_for_plan,
    render_for_registration,
    resolve_recipients,
)
from tests._factories import (
    EventFactory,
    RegistrationFactory,
    SessionFactory,
    UserFactory,
)


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


def dt(s: str) -> datetime:
    """Parse an ISO-like datetime string into a UTC-aware datetime.

    :param s: A datetime string in ``YYYY-MM-DD HH:MM`` format.
    :returns: A timezone-aware datetime in UTC.
    """
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


@pytest.fixture
def event(db):
    """An event with two fee types so fee-type filters can be exercised."""
    e = EventFactory(
        start_date=dt("2026-09-01 00:00").date(),
        end_date=dt("2026-09-05 00:00").date(),
        registration_start_date=dt("2026-03-01 00:00").date(),
        registration_deadline=dt("2026-08-31 23:59"),
        registration_early_deadline=None,
        registration_onsite_deadline=None,
    )
    Fee.objects.create(event=e, type="regular", value=100)
    Fee.objects.create(event=e, type="student", value=50)
    return e


def _make_registration(event, *, fee_type="regular", user=None, is_accepted=True, paid=0):
    """Create a registration with deterministic creation time and optional payment.

    :param event: The event to register for.
    :param fee_type: The fee type code.
    :param user: An existing user, or None to create a fresh one.
    :param is_accepted: The acceptance state (True/False/None).
    :param paid: Amount paid, set after creation to control saldo.
    :returns: The created Registration.
    """
    user = user or UserFactory()
    with patch("django.utils.timezone.now", return_value=dt("2026-07-01 12:00")):
        reg = RegistrationFactory(event=event, user=user, fee_type=fee_type)
    if is_accepted is not True:
        reg.is_accepted = is_accepted
    if paid:
        reg.paid = paid
    reg.save()
    reg.refresh_from_db()
    return reg


def _plan(event, **kwargs):
    """Build an in-memory EmailPlan without saving (resolution does not require pk).

    :param event: The event the plan belongs to.
    :param kwargs: Overrides for subject, body, filters, from_email, etc.
    :returns: An unsaved EmailPlan instance.
    """
    from evan.models import EmailPlan

    defaults = {
        "name": "Test plan",
        "subject": "Hello {{ user.first_name }}",
        "body": "Welcome to {{ event.name }}!",
        "from_email": "UGent <evan@ugent.be>",
        "filters": {},
    }
    defaults.update(kwargs)
    return EmailPlan(event=event, **defaults)


# ---------------------------------------------------------------------------
# Base resolution
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestResolveRecipientsBase:
    """The base queryset excludes rejected registrations and includes everyone else."""

    def test_no_filters_returns_all_accepted_registrations(self, event) -> None:
        r1 = _make_registration(event)
        r2 = _make_registration(event, user=UserFactory())
        _make_registration(event, user=UserFactory(), is_accepted=False)

        plan = _plan(event)
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {r1.pk, r2.pk}

    def test_rejected_registrations_excluded(self, event) -> None:
        accepted = _make_registration(event)
        _make_registration(event, user=UserFactory(), is_accepted=False)

        plan = _plan(event)
        pks = list(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == [accepted.pk]

    def test_pending_registrations_excluded(self, event) -> None:
        accepted = _make_registration(event)
        _make_registration(event, user=UserFactory(), is_accepted=None)

        plan = _plan(event)
        pks = list(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == [accepted.pk]


# ---------------------------------------------------------------------------
# Fee-type filter
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestResolveRecipientsFeeType:
    """fee_types restricts to registrations whose fee_type is in the list."""

    def test_filter_by_single_fee_type(self, event) -> None:
        regular = _make_registration(event, fee_type="regular")
        _make_registration(event, user=UserFactory(), fee_type="student")

        plan = _plan(event, filters={"fee_types": ["regular"]})
        pks = list(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == [regular.pk]

    def test_filter_by_multiple_fee_types(self, event) -> None:
        r1 = _make_registration(event, fee_type="regular")
        r2 = _make_registration(event, user=UserFactory(), fee_type="student")

        plan = _plan(event, filters={"fee_types": ["regular", "student"]})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {r1.pk, r2.pk}

    def test_empty_fee_types_means_all(self, event) -> None:
        r1 = _make_registration(event, fee_type="regular")
        r2 = _make_registration(event, user=UserFactory(), fee_type="student")

        plan = _plan(event, filters={"fee_types": []})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {r1.pk, r2.pk}


# ---------------------------------------------------------------------------
# Session filter
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestResolveRecipientsSessions:
    """sessions filter with match=all / match=any."""

    def test_match_any_returns_registrations_in_at_least_one_session(self, event) -> None:
        s1 = SessionFactory(event=event)
        s2 = SessionFactory(event=event)
        in_s1 = _make_registration(event)
        in_s1.sessions.add(s1)
        in_s2 = _make_registration(event, user=UserFactory())
        in_s2.sessions.add(s2)
        _make_registration(event, user=UserFactory())  # in none

        plan = _plan(event, filters={"sessions": {"ids": [s1.pk, s2.pk], "match": "any"}})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {in_s1.pk, in_s2.pk}

    def test_match_all_returns_only_registrations_in_every_listed_session(self, event) -> None:
        s1 = SessionFactory(event=event)
        s2 = SessionFactory(event=event)
        in_both = _make_registration(event)
        in_both.sessions.add(s1, s2)
        in_one = _make_registration(event, user=UserFactory())
        in_one.sessions.add(s1)

        plan = _plan(event, filters={"sessions": {"ids": [s1.pk, s2.pk], "match": "all"}})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {in_both.pk}

    def test_empty_session_ids_means_no_filter(self, event) -> None:
        r1 = _make_registration(event)
        r2 = _make_registration(event, user=UserFactory())

        plan = _plan(event, filters={"sessions": {"ids": [], "match": "all"}})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {r1.pk, r2.pk}


# ---------------------------------------------------------------------------
# Session-days filter
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestResolveRecipientsSessionDays:
    """session_days filters by the date of sessions a registration attends."""

    def test_filter_by_session_day(self, event) -> None:
        day1 = dt("2026-09-02 10:00")
        day2 = dt("2026-09-03 10:00")
        s1 = SessionFactory(event=event, start_at=day1)
        s2 = SessionFactory(event=event, start_at=day2)
        on_day1 = _make_registration(event)
        on_day1.sessions.add(s1)
        on_day2 = _make_registration(event, user=UserFactory())
        on_day2.sessions.add(s2)
        _make_registration(event, user=UserFactory())  # no sessions

        plan = _plan(event, filters={"session_days": ["2026-09-02"]})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {on_day1.pk}

    def test_empty_session_days_means_no_filter(self, event) -> None:
        r1 = _make_registration(event)

        plan = _plan(event, filters={"session_days": []})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {r1.pk}


# ---------------------------------------------------------------------------
# Payment-status filter
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestResolveRecipientsPaymentStatus:
    """payment_status filters by saldo sign (paid = saldo >= 0, unpaid = saldo < 0)."""

    def test_paid_returns_only_settled_registrations(self, event) -> None:
        paid = _make_registration(event, paid=100)  # saldo = 0
        _make_registration(event, user=UserFactory())  # saldo = -100

        plan = _plan(event, filters={"payment_status": "paid"})
        pks = list(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == [paid.pk]

    def test_unpaid_returns_only_outstanding_registrations(self, event) -> None:
        _make_registration(event, paid=100)
        unpaid = _make_registration(event, user=UserFactory())

        plan = _plan(event, filters={"payment_status": "unpaid"})
        pks = list(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == [unpaid.pk]

    def test_null_payment_status_means_all(self, event) -> None:
        r1 = _make_registration(event, paid=100)
        r2 = _make_registration(event, user=UserFactory())

        plan = _plan(event, filters={"payment_status": None})
        pks = set(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == {r1.pk, r2.pk}


# ---------------------------------------------------------------------------
# Combined filters
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestResolveRecipientsCombined:
    """Multiple active dimensions intersect."""

    def test_fee_type_and_payment_status_intersect(self, event) -> None:
        regular_paid = _make_registration(event, fee_type="regular", paid=100)
        _make_registration(event, user=UserFactory(), fee_type="regular")
        _make_registration(event, user=UserFactory(), fee_type="student", paid=50)

        plan = _plan(event, filters={"fee_types": ["regular"], "payment_status": "paid"})
        pks = list(resolve_recipients(plan).values_list("pk", flat=True))

        assert pks == [regular_paid.pk]


# ---------------------------------------------------------------------------
# Random registration (preview)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetRandomRegistration:
    """get_random_registration returns a matching registration or None."""

    def test_returns_a_matching_registration(self, event) -> None:
        reg = _make_registration(event)

        plan = _plan(event)
        result = get_random_registration(plan)

        assert result is not None
        assert result.pk == reg.pk

    def test_returns_none_when_no_match(self, event) -> None:
        plan = _plan(event, filters={"fee_types": ["nonexistent"]})
        assert get_random_registration(plan) is None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRenderForRegistration:
    """render_for_registration substitutes event and user variables."""

    def test_renders_subject_and_body(self, event) -> None:
        reg = _make_registration(event)

        plan = _plan(
            event,
            subject="Hello {{ user.first_name }}",
            body="Welcome to {{ event.name }}!",
        )
        subject, body = render_for_registration(plan, reg)

        assert subject == f"Hello {reg.user.first_name}"
        assert body == f"Welcome to {event.name}!"

    def test_session_context_when_session_filtered(self, event) -> None:
        session = SessionFactory(event=event, title="Welcome reception")
        reg = _make_registration(event)
        reg.sessions.add(session)

        plan = _plan(
            event,
            subject="Update on {{ session.title }}",
            body="See you at {{ session.title }}!",
            filters={"sessions": {"ids": [session.pk], "match": "any"}},
        )
        subject, body = render_for_registration(plan, reg)

        assert subject == "Update on Welcome reception"
        assert body == "See you at Welcome reception!"

    def test_session_context_none_when_not_session_filtered(self, event) -> None:
        reg = _make_registration(event)

        plan = _plan(event, body="Session is {{ session }}")
        _, body = render_for_registration(plan, reg)

        assert body == "Session is None"


# ---------------------------------------------------------------------------
# execute_plan
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExecutePlan:
    """execute_plan creates one EmailLog per recipient and marks the plan sent."""

    def test_creates_one_log_per_recipient_and_marks_sent(self, event) -> None:
        r1 = _make_registration(event)
        r2 = _make_registration(event, user=UserFactory())
        plan = _plan(event)
        plan.save()

        count = execute_plan(plan)

        assert count == 2
        plan.refresh_from_db()
        assert plan.sent_at is not None
        logs = logs_for_plan(plan)
        assert logs.count() == 2
        to_addresses = {log.to[0] for log in logs}
        assert to_addresses == {r1.user.email, r2.user.email}

    def test_logs_tagged_with_type_emailplan(self, event) -> None:
        _make_registration(event)
        plan = _plan(event)
        plan.save()

        execute_plan(plan)

        log = logs_for_plan(plan).get()
        assert "type:emailplan" in log.tags
        assert f"event.id:{event.pk}" in log.tags

    def test_no_recipients_creates_zero_logs_but_still_marks_sent(self, event) -> None:
        plan = _plan(event, filters={"fee_types": ["nonexistent"]})
        plan.save()

        count = execute_plan(plan)

        assert count == 0
        plan.refresh_from_db()
        assert plan.sent_at is not None
        assert logs_for_plan(plan).count() == 0

    def test_already_sent_plan_is_not_executed_again(self, event) -> None:
        _make_registration(event)
        plan = _plan(event)
        plan.save()
        execute_plan(plan)
        assert logs_for_plan(plan).count() == 1

        # Second call should claim nothing (sent_at already set).
        count = execute_plan(plan)

        assert count == 0
        assert logs_for_plan(plan).count() == 1

    def test_renders_template_per_recipient(self, event) -> None:
        r1 = _make_registration(event)
        r2 = _make_registration(event, user=UserFactory())
        plan = _plan(event, subject="Hi {{ user.first_name }}", body="Hi {{ user.first_name }}!")
        plan.save()

        execute_plan(plan)

        logs = logs_for_plan(plan).order_by("to")
        subjects = [log.subject for log in logs]
        assert f"Hi {r1.user.first_name}" in subjects
        assert f"Hi {r2.user.first_name}" in subjects
