from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError


def convdate(date, format="%Y-%m-%d"):
    return datetime.strptime(date, format).replace(tzinfo=UTC).date()


def convtime(date, format="%Y-%m-%d %H:%M"):
    return datetime.strptime(date, format).replace(tzinfo=UTC)


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
def test_invalid_dates(test_event, start_date, end_date, reg_start_date, reg_early_deadline, reg_deadline):
    test_event.start_date = convdate(start_date)
    test_event.end_date = convdate(end_date)
    test_event.registration_start_date = convdate(reg_start_date)
    test_event.registration_early_deadline = convtime(reg_early_deadline) if reg_early_deadline else None
    test_event.registration_deadline = convtime(reg_deadline)

    with pytest.raises(ValidationError):
        test_event.clean()
