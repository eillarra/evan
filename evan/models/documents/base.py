from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ImportantDate(BaseModel):
    """An important date for an event or session."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    label: str
    format: Literal["date", "range", "month"] = "date"
    start_date: date
    end_date: date | None = None
    aoe: bool = True


class Person(BaseModel):
    """A person."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    name: str
    affiliation: str | None = None
    country_code: str | None = None
    email: str | None = None
