from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError


def convdate(date, format="%Y-%m-%d"):
    """Convert a date string to a UTC-aware date object.

    :param date: A date string.
    :param format: The format string.
    :returns: A date object.
    """
    return datetime.strptime(date, format).replace(tzinfo=UTC).date()


def convtime(date, format="%Y-%m-%d %H:%M"):
    """Convert a datetime string to a UTC-aware datetime object.

    :param date: A datetime string.
    :param format: The format string.
    :returns: A UTC-aware datetime object.
    """
    return datetime.strptime(date, format).replace(tzinfo=UTC)


# ---------------------------------------------------------------------------
# Date validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "start_date, end_date, reg_start_date, reg_early_deadline, reg_deadline",
    [
        ("2024-01-03", "2024-01-02", "2024-01-01", None, "2024-01-02 23:59"),
        ("2024-01-01", "2024-01-03", "2024-01-05", None, "2024-01-03 23:59"),
        ("2024-02-01", "2024-02-03", "2024-01-05", None, "2024-01-01 23:59"),
        ("2024-02-01", "2024-02-03", "2024-01-01", "2024-01-15 23:59", "2024-01-05 23:59"),
        ("2024-02-01", "2024-02-03", "2024-01-05", "2024-01-01 23:59", "2024-01-15 23:59"),
    ],
)
def test_invalid_dates(t_event, start_date, end_date, reg_start_date, reg_early_deadline, reg_deadline):
    """Event with invalid date combinations raises ValidationError."""
    t_event.start_date = convdate(start_date)
    t_event.end_date = convdate(end_date)
    t_event.registration_start_date = convdate(reg_start_date)
    t_event.registration_early_deadline = convtime(reg_early_deadline) if reg_early_deadline else None
    t_event.registration_deadline = convtime(reg_deadline)

    with pytest.raises(ValidationError):
        t_event.clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "reg_deadline, reg_onsite_deadline",
    [
        # on-site deadline at same time as regular deadline
        ("2024-08-31 23:59", "2024-08-31 23:59"),
        # on-site deadline before regular deadline
        ("2024-08-31 23:59", "2024-08-01 12:00"),
    ],
)
def test_invalid_onsite_deadline(t_event, reg_deadline, reg_onsite_deadline):
    """On-site deadline that is not strictly after the regular deadline raises ValidationError."""
    t_event.registration_deadline = convtime(reg_deadline)
    t_event.registration_onsite_deadline = convtime(reg_onsite_deadline)

    with pytest.raises(ValidationError):
        t_event.clean()


# ---------------------------------------------------------------------------
# Registration window (is_open_for_registration)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_registration_is_open_during_onsite_period(t_event):
    """Event is still open for registration during the on-site window."""
    t_event.registration_start_date = convdate("2026-08-01")
    t_event.registration_deadline = convtime("2026-08-31 23:59")
    t_event.registration_onsite_deadline = convtime("2026-09-05 18:00")
    t_event.save()
    t_event.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=convtime("2026-09-02 10:00")):
        assert t_event.is_open_for_registration is True


@pytest.mark.django_db
def test_registration_is_closed_after_onsite_deadline(t_event):
    """Event is closed for registration after the on-site deadline passes."""
    t_event.registration_start_date = convdate("2026-08-01")
    t_event.registration_deadline = convtime("2026-08-31 23:59")
    t_event.registration_onsite_deadline = convtime("2026-09-05 18:00")
    t_event.save()
    t_event.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=convtime("2026-09-05 18:01")):
        assert t_event.is_open_for_registration is False


@pytest.mark.django_db
def test_registration_is_closed_after_regular_deadline_when_no_onsite(t_event):
    """Without an on-site deadline, registration closes at the regular deadline."""
    t_event.registration_start_date = convdate("2026-08-01")
    t_event.registration_deadline = convtime("2026-08-31 23:59")
    t_event.registration_onsite_deadline = None
    t_event.save()
    t_event.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=convtime("2026-09-01 00:01")):
        assert t_event.is_open_for_registration is False


# ---------------------------------------------------------------------------
# Pricing period flags (is_early, is_onsite)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_event_is_early_before_early_deadline(t_event):
    """Event reports early pricing when current time is before early deadline."""
    t_event.registration_early_deadline = convtime("2026-06-29 23:59")
    t_event.save()

    with patch("django.utils.timezone.now", return_value=convtime("2026-05-01 12:00")):
        assert t_event.is_early is True


@pytest.mark.django_db
def test_event_is_not_early_after_early_deadline(t_event):
    """Event does not report early pricing after the early deadline."""
    t_event.registration_early_deadline = convtime("2026-06-29 23:59")
    t_event.save()

    with patch("django.utils.timezone.now", return_value=convtime("2026-06-30 00:00")):
        assert t_event.is_early is False


@pytest.mark.django_db
def test_event_is_onsite_between_regular_and_onsite_deadlines(t_event):
    """Event reports on-site pricing when current time is between the regular and on-site deadlines."""
    t_event.registration_deadline = convtime("2026-08-31 23:59")
    t_event.registration_onsite_deadline = convtime("2026-09-05 18:00")
    t_event.save()

    with patch("django.utils.timezone.now", return_value=convtime("2026-09-02 10:00")):
        assert t_event.is_onsite is True


@pytest.mark.django_db
def test_event_is_not_onsite_before_regular_deadline(t_event):
    """Event does not report on-site pricing while the regular window is still open."""
    t_event.registration_deadline = convtime("2026-08-31 23:59")
    t_event.registration_onsite_deadline = convtime("2026-09-05 18:00")
    t_event.save()

    with patch("django.utils.timezone.now", return_value=convtime("2026-08-15 12:00")):
        assert t_event.is_onsite is False


@pytest.mark.django_db
def test_event_is_not_onsite_when_no_onsite_deadline_configured(t_event):
    """Without an on-site deadline, on-site pricing is never active."""
    t_event.registration_onsite_deadline = None
    t_event.save()

    with patch("django.utils.timezone.now", return_value=convtime("2026-09-02 10:00")):
        assert t_event.is_onsite is False


@pytest.mark.django_db
def test_event_registration_configuration_supports_form_fields(t_event):
    """Event registration configuration supports global form fields."""
    t_event.registration_config = {
        "form_fields": [
            {
                "code": "paper_id",
                "label": "Paper ID",
                "field_type": "text",
                "required": True,
            }
        ]
    }

    t_event.save()
    t_event.refresh_from_db()

    config = t_event.registration_configuration
    assert "form_fields" in config
    assert config["form_fields"][0]["code"] == "paper_id"


@pytest.mark.django_db
def test_event_registration_configuration_accompanying_persons_defaults_true(t_event):
    """Accompanying persons section is enabled by default for backward compatibility."""
    t_event.registration_config = {}
    t_event.save()
    t_event.refresh_from_db()

    assert t_event.registration_configuration["accompanying_persons"] is True


@pytest.mark.django_db
def test_event_registration_configuration_can_disable_accompanying_persons(t_event):
    """Organisers can disable the accompanying persons section on the registration form."""
    t_event.registration_config = {"accompanying_persons": False}
    t_event.save()
    t_event.refresh_from_db()

    assert t_event.registration_configuration["accompanying_persons"] is False


# ---------------------------------------------------------------------------
# Payment configuration (allows_payments, allows_invoices, ugent_bridge)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEventAllowsPayments:
    """allows_payments reflects the presence of a Worldline salt and an optional activation date."""

    def test_false_without_salt(self, t_event) -> None:
        # A ugent payment block requires salt at config-validation
        # time, so the only way to reach allows_payments without a salt is to
        # have no payment block at all — which the pydantic validator keeps
        # as a plain dict and worldline returns {} for.
        t_event.config = {"payments": {"type": "stripe", "wbs_element": "WBS", "stripe_secret": "sk_test"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.allows_payments is False

    def test_true_with_salt_and_no_activation_date(self, t_event) -> None:
        t_event.config = {"payments": {"type": "ugent", "wbs_element": "WBS", "salt": "s4lt"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.allows_payments is True

    def test_false_when_activation_date_in_future(self, t_event) -> None:
        t_event.config = {
            "payments": {
                "type": "ugent",
                "wbs_element": "WBS",
                "salt": "s4lt",
                "activation_date": "2099-01-01",
            },
        }
        t_event.save()
        t_event.refresh_from_db()

        with patch("django.utils.timezone.now", return_value=convtime("2026-08-15 12:00")):
            assert t_event.allows_payments is False

    def test_true_when_activation_date_in_past(self, t_event) -> None:
        t_event.config = {
            "payments": {
                "type": "ugent",
                "wbs_element": "WBS",
                "salt": "s4lt",
                "activation_date": "2026-01-01",
            },
        }
        t_event.save()
        t_event.refresh_from_db()

        with patch("django.utils.timezone.now", return_value=convtime("2026-08-15 12:00")):
            assert t_event.allows_payments is True

    def test_false_when_no_payment_config(self, t_event) -> None:
        t_event.config = {}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.allows_payments is False


@pytest.mark.django_db
class TestEventAllowsInvoices:
    """allows_invoices mirrors the allow_invoices flag in the Worldline payment config."""

    def test_true_when_allow_invoices_set(self, t_event) -> None:
        t_event.config = {"payments": {"type": "ugent", "wbs_element": "WBS", "salt": "s4lt", "allow_invoices": True}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.allows_invoices is True

    def test_false_when_allow_invoices_absent(self, t_event) -> None:
        t_event.config = {"payments": {"type": "ugent", "wbs_element": "WBS", "salt": "s4lt"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.allows_invoices is True  # defaults to True in UgentPaymentsConfig

    def test_false_when_allow_invoices_false(self, t_event) -> None:
        t_event.config = {"payments": {"type": "ugent", "wbs_element": "WBS", "salt": "s4lt", "allow_invoices": False}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.allows_invoices is False

    def test_false_when_no_payment_config(self, t_event) -> None:
        t_event.config = {}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.allows_invoices is False


@pytest.mark.django_db
class TestEventUGentBridgeProperty:
    """ugent_bridge returns the payment config dict for ugent type, empty dict otherwise."""

    def test_ugent_type_returns_payments_dict(self, t_event) -> None:
        t_event.config = {"payments": {"type": "ugent", "wbs_element": "WBS", "salt": "s4lt"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.ugent_bridge["type"] == "ugent"
        assert t_event.ugent_bridge["salt"] == "s4lt"

    def test_no_payments_returns_empty_dict(self, t_event) -> None:
        t_event.config = {}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.ugent_bridge == {}


# ---------------------------------------------------------------------------
# Contact email, social event bundle, active/closed state
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEventContactEmail:
    """contact_email falls back to the default address when the event has none."""

    def test_returns_event_email_when_set(self, t_event) -> None:
        t_event.email = "organiser@example.com"
        t_event.save()

        assert t_event.contact_email == "organiser@example.com"

    def test_falls_back_to_default_when_empty(self, t_event) -> None:
        t_event.email = ""
        t_event.save()

        assert t_event.contact_email == "evan@ugent.be"


@pytest.mark.django_db
class TestEventSocialEventBundle:
    """has_social_event_bundle is True only when a bundle fee is configured."""

    def test_true_when_fee_positive(self, t_event) -> None:
        t_event.social_event_bundle_fee = 25
        t_event.save()

        assert t_event.has_social_event_bundle is True

    def test_false_when_fee_zero(self, t_event) -> None:
        t_event.social_event_bundle_fee = 0
        t_event.save()

        assert t_event.has_social_event_bundle is False


@pytest.mark.django_db
class TestEventActiveClosedState:
    """is_active and is_closed depend on the current date relative to the event window."""

    def test_is_active_during_event_window(self, t_event) -> None:
        t_event.start_date = convdate("2026-09-01")
        t_event.end_date = convdate("2026-09-05")
        t_event.save()

        with patch("django.utils.timezone.now", return_value=convtime("2026-09-03 12:00")):
            assert t_event.is_active is True
            assert t_event.is_closed is False

    def test_not_active_before_event_starts(self, t_event) -> None:
        t_event.start_date = convdate("2026-09-01")
        t_event.end_date = convdate("2026-09-05")
        t_event.save()

        with patch("django.utils.timezone.now", return_value=convtime("2026-08-15 12:00")):
            assert t_event.is_active is False
            assert t_event.is_closed is False

    def test_is_closed_after_event_ends(self, t_event) -> None:
        t_event.start_date = convdate("2026-09-01")
        t_event.end_date = convdate("2026-09-05")
        t_event.save()

        with patch("django.utils.timezone.now", return_value=convtime("2026-09-10 12:00")):
            assert t_event.is_active is False
            assert t_event.is_closed is True


# ---------------------------------------------------------------------------
# Abstract submission window (is_open_for_abstract_submission)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEventAbstractSubmissionWindow:
    """is_open_for_abstract_submission reads the abstracts config from custom_fields."""

    def test_open_during_configured_window(self, t_event) -> None:
        t_event.custom_fields = {
            "abstracts": {"submission_start_date": "2026-01-01", "submission_deadline": "2026-12-31T23:59"}
        }
        t_event.save()
        t_event.refresh_from_db()

        with patch("django.utils.timezone.now", return_value=convtime("2026-08-15 12:00")):
            assert t_event.is_open_for_abstract_submission is True

    def test_closed_before_start_date(self, t_event) -> None:
        t_event.custom_fields = {
            "abstracts": {"submission_start_date": "2026-12-01", "submission_deadline": "2026-12-31T23:59"}
        }
        t_event.save()
        t_event.refresh_from_db()

        with patch("django.utils.timezone.now", return_value=convtime("2026-08-15 12:00")):
            assert t_event.is_open_for_abstract_submission is False

    def test_closed_after_deadline(self, t_event) -> None:
        t_event.custom_fields = {
            "abstracts": {"submission_start_date": "2026-01-01", "submission_deadline": "2026-01-31T23:59"}
        }
        t_event.save()
        t_event.refresh_from_db()

        with patch("django.utils.timezone.now", return_value=convtime("2026-08-15 12:00")):
            assert t_event.is_open_for_abstract_submission is False

    def test_false_when_no_abstracts_config(self, t_event) -> None:
        t_event.custom_fields = {}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.is_open_for_abstract_submission is False

    def test_false_when_malformed_config(self, t_event) -> None:
        t_event.custom_fields = {"abstracts": {"submission_start_date": "not-a-date"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.is_open_for_abstract_submission is False

    def test_false_when_deadline_missing(self, t_event) -> None:
        t_event.custom_fields = {"abstracts": {"submission_start_date": "2026-01-01"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.is_open_for_abstract_submission is False

    def test_false_when_abstracts_not_a_dict(self, t_event) -> None:
        t_event.custom_fields = {"abstracts": "not-a-dict"}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.is_open_for_abstract_submission is False

    def test_unexpected_exception_is_not_swallowed(self, t_event) -> None:
        t_event.custom_fields = {
            "abstracts": {"submission_start_date": "2026-01-01", "submission_deadline": "2026-12-31T23:59"}
        }
        t_event.save()
        t_event.refresh_from_db()

        class Boom(Exception):
            pass

        with (
            patch.object(type(t_event), "abstracts_config", new=property(lambda self: (_ for _ in ()).throw(Boom()))),
            pytest.raises(Boom),
        ):
            _ = t_event.is_open_for_abstract_submission


# ---------------------------------------------------------------------------
# Abstracts config accessor (abstracts_config)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEventAbstractsConfigAccessor:
    """abstracts_config centralises custom_fields['abstracts'] access."""

    def test_returns_config_dict(self, t_event) -> None:
        t_event.custom_fields = {"abstracts": {"submission_start_date": "2026-01-01"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.abstracts_config == {"submission_start_date": "2026-01-01"}

    def test_returns_empty_dict_when_missing(self, t_event) -> None:
        t_event.custom_fields = {}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.abstracts_config == {}

    def test_returns_empty_dict_when_not_a_dict(self, t_event) -> None:
        t_event.custom_fields = {"abstracts": ["not", "a", "dict"]}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.abstracts_config == {}


# ---------------------------------------------------------------------------
# Abstract reviewers (abstract_reviewers)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEventAbstractReviewers:
    """abstract_reviewers returns the configured reviewers or an empty queryset."""

    def test_returns_reviewers(self, t_event) -> None:
        from tests._factories import UserFactory

        user = UserFactory()
        t_event.custom_fields = {"abstracts": {"reviewers": [{"id": user.id}]}}
        t_event.save()
        t_event.refresh_from_db()

        assert list(t_event.abstract_reviewers) == [user]

    def test_empty_when_no_reviewers(self, t_event) -> None:
        t_event.custom_fields = {}
        t_event.save()
        t_event.refresh_from_db()

        assert list(t_event.abstract_reviewers) == []

    def test_empty_when_reviewers_not_a_list(self, t_event) -> None:
        t_event.custom_fields = {"abstracts": {"reviewers": "not-a-list"}}
        t_event.save()
        t_event.refresh_from_db()

        assert list(t_event.abstract_reviewers) == []


# ---------------------------------------------------------------------------
# Email template lookup (get_email_template)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEventGetEmailTemplate:
    """get_email_template returns the event-specific template, then the global fallback, then None."""

    def test_event_specific_template_returned_first(self, t_event) -> None:
        from tests._factories import EmailTemplateFactory

        event_tpl = EmailTemplateFactory(code="registration.created", event=t_event)
        EmailTemplateFactory(code="registration.created", event=None)

        assert t_event.get_email_template(code="registration.created") == event_tpl

    def test_global_fallback_returned_when_no_event_template(self, t_event) -> None:
        from tests._factories import EmailTemplateFactory

        global_tpl = EmailTemplateFactory(code="registration.created", event=None)

        assert t_event.get_email_template(code="registration.created") == global_tpl

    def test_none_when_no_template_exists(self, t_event) -> None:
        assert t_event.get_email_template(code="nonexistent.code") is None
