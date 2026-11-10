from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


def blank_to_none[T](value: T) -> T | None:
    """Treat blank or whitespace-only text as no value.

    Extra-data schemas use this for optional free-text fields: a JSON ``""`` or
    ``"   "`` becomes ``None`` so clients only have to handle one empty state.

    :param value: The raw value from the extra data mapping.
    :returns: None when the value is a blank string, otherwise the value unchanged.
    """
    if isinstance(value, str) and not value.strip():
        return None
    return value


class ImportantDate(BaseModel):
    """An important date for an event or session."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    label: str
    format: Literal["date", "range", "month"] = "date"
    start_date: date
    end_date: date | None = None
    aoe: bool = True


class Person(BaseModel):
    """A person."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    first_name: str
    last_name: str
    affiliation: str | None = None
    email: str | None = None


class Committee(BaseModel):
    """A committee."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    name: str
    members: list[Person]
    sorting: Literal["first_name", "last_name"] = "last_name"
    display: Literal["full", "list"] = "list"
