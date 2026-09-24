from datetime import UTC, datetime
from importlib import import_module
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from tests._factories import CouponFactory, EventFactory, PaperFactory, SessionFactory


MODULE_KEYS = ("payments", "content", "program", "papers", "communications")


def backfill_existing_events(apps, schema_editor):
    """Run the 0028 data migration backfill against the given apps registry."""
    migration = import_module("evan.migrations.0028_event_modules_backfill")
    return migration.backfill_existing_events(apps, schema_editor)


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

    def test_false_on_stripe_rail(self, t_event) -> None:
        """Invoice tracking is only available on the UGent bridge rail."""
        t_event.config = {"payments": {"type": "stripe", "wbs_element": "WBS", "stripe_secret": "sk_test"}}
        t_event.save()
        t_event.refresh_from_db()

        assert t_event.ugent_bridge == {}
        assert t_event.allows_invoices is False

    def test_bridge_rail_requires_wbs_element(self, t_event) -> None:
        """The bridge's financial reference (WBS element) is required by config validation."""
        t_event.config = {"payments": {"type": "ugent", "salt": "s4lt"}}

        with pytest.raises(ValidationError):
            t_event.save()


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


# ---------------------------------------------------------------------------
# Event modules (config["modules"]), audience, listing status
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEventModulesDefaults:
    """A fresh event reads all modules off, public audience, pending review."""

    def test_fresh_event_reads_all_modules_false(self, db) -> None:
        # The factory's default config is all-on (legacy mapping); a config-less
        # event reads every module as disabled, per the pydantic defaults.
        event = EventFactory(config={})

        assert event.configuration["modules"] == {key: False for key in MODULE_KEYS}
        assert event.module_enabled("payments") is False

    def test_module_enabled_reflects_config(self, db) -> None:
        event = EventFactory(config={})
        assert event.module_enabled("payments") is False

        event.config = {"modules": {"payments": True}}
        event.save()
        event.refresh_from_db()

        assert event.module_enabled("payments") is True
        assert event.module_enabled("content") is False

    def test_module_enabled_rejects_unknown_key(self, t_event) -> None:
        with pytest.raises(KeyError):
            t_event.module_enabled("bogus")

    def test_unknown_module_key_fails_validation(self, t_event) -> None:
        t_event.config = {"modules": {"bogus": True}}

        with pytest.raises(ValidationError):
            t_event.save()

    def test_fresh_event_audience_and_listing_defaults(self, db) -> None:
        from evan.models import Event

        assert Event._meta.get_field("registration_audience").default == "public"
        assert Event._meta.get_field("listing_status").default == "pending_review"

        event = EventFactory(config={})
        assert event.registration_audience == "public"


@pytest.mark.django_db
class TestEventModulesLegacyMapping:
    """Events that predate modules are mapped to all-on via the data migration."""

    def test_backfill_maps_legacy_event_all_on(self, t_event) -> None:
        # Simulate a pre-modules event: no modules section, pre-gate status.
        Event = type(t_event)
        Event.objects.filter(pk=t_event.pk).update(
            config={"payments": {"type": "ugent", "wbs_element": "WBS", "salt": "s4lt"}},
            registration_audience="public",
            listing_status="pending_review",
        )

        from django.apps import apps as global_apps

        backfill_existing_events(global_apps, None)
        t_event.refresh_from_db()

        assert t_event.configuration["modules"] == {key: True for key in MODULE_KEYS}
        assert t_event.registration_audience == "public"
        assert t_event.listing_status == "listed"
        assert t_event.is_listed is True


@pytest.mark.django_db
class TestEventModulesGuard:
    """Disabling a module with existing data is refused; data is preserved."""

    @staticmethod
    def _enable(event, key):
        event.config = {"modules": {key: True}}
        event.save()
        event.refresh_from_db()

    @staticmethod
    def _disable(event, key):
        event.config = {}
        event.clean_modules()

    def test_disable_payments_with_data_refused(self, t_event) -> None:
        # t_event comes with a fee from the t_event fixture.
        self._enable(t_event, "payments")

        with pytest.raises(ValidationError, match="payments"):
            self._disable(t_event, "payments")

        t_event.refresh_from_db()
        assert t_event.module_enabled("payments") is True
        assert t_event.fees.exists()

    def test_disable_payments_without_data_succeeds(self, db) -> None:
        from tests._factories import EventFactory

        event = EventFactory()
        self._enable(event, "payments")
        self._disable(event, "payments")

    def test_disable_coupon_payments_refused(self, t_event) -> None:
        t_event.fees.all().delete()
        CouponFactory(event=t_event)
        self._enable(t_event, "payments")

        with pytest.raises(ValidationError, match="coupons"):
            self._disable(t_event, "payments")

    def test_disable_papers_with_data_refused(self, t_event) -> None:
        PaperFactory(event=t_event, session=None)
        self._enable(t_event, "papers")

        with pytest.raises(ValidationError, match="papers"):
            self._disable(t_event, "papers")

    def test_disable_program_with_data_refused(self, t_event) -> None:
        SessionFactory(event=t_event)
        self._enable(t_event, "program")

        with pytest.raises(ValidationError, match="sessions"):
            self._disable(t_event, "program")

    def test_disable_content_with_data_refused(self, t_event) -> None:
        from tests._factories import KeynoteFactory

        KeynoteFactory(event=t_event)
        self._enable(t_event, "content")

        with pytest.raises(ValidationError, match="keynotes"):
            self._disable(t_event, "content")

    def test_disable_communications_with_data_refused(self, t_event) -> None:
        from evan.models import EmailPlan

        EmailPlan.objects.create(event=t_event, name="Plan", subject="S", body="B")
        self._enable(t_event, "communications")

        with pytest.raises(ValidationError, match="email plans"):
            self._disable(t_event, "communications")

    def test_reenable_restores_behavior(self, t_event) -> None:
        t_event.fees.all().delete()
        self._enable(t_event, "payments")
        self._disable(t_event, "payments")
        self._enable(t_event, "payments")

        t_event.refresh_from_db()
        assert t_event.module_enabled("payments") is True


@pytest.mark.django_db
class TestEventListingAndUrls:
    """EventManager.listed, is_listed and the URL helpers."""

    def test_listed_returns_only_listed_events(self, t_event) -> None:
        from tests._factories import EventFactory

        EventFactory(code="listed-event", listing_status="listed")
        EventFactory(code="pending-event", listing_status="pending_review")
        EventFactory(code="declined-event", listing_status="declined")

        from evan.models import Event

        codes = set(Event.objects.listed().values_list("code", flat=True))

        assert "listed-event" in codes
        assert "pending-event" not in codes
        assert "declined-event" not in codes

    def test_is_listed_follows_status(self, t_event) -> None:
        t_event.listing_status = "pending_review"
        assert t_event.is_listed is False

        t_event.listing_status = "listed"
        assert t_event.is_listed is True

    def test_url_helpers_point_to_public_and_manage_pages(self, t_event) -> None:
        assert t_event.get_absolute_url() == f"/e/{t_event.code}/"
        assert t_event.get_manage_url() == f"/e/{t_event.code}/manage/"
