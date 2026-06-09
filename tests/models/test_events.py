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
    t_event.registration_deadline = convtime("2026-08-31 23:59")
    t_event.registration_onsite_deadline = convtime("2026-09-05 18:00")
    t_event.save()
    t_event.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=convtime("2026-09-02 10:00")):
        assert t_event.is_open_for_registration is True


@pytest.mark.django_db
def test_registration_is_closed_after_onsite_deadline(t_event):
    """Event is closed for registration after the on-site deadline passes."""
    t_event.registration_deadline = convtime("2026-08-31 23:59")
    t_event.registration_onsite_deadline = convtime("2026-09-05 18:00")
    t_event.save()
    t_event.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=convtime("2026-09-05 18:01")):
        assert t_event.is_open_for_registration is False


@pytest.mark.django_db
def test_registration_is_closed_after_regular_deadline_when_no_onsite(t_event):
    """Without an on-site deadline, registration closes at the regular deadline."""
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
