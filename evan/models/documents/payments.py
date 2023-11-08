from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BasePaymentsConfig(BaseModel):
    """Payment configuration."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    activation_date: date | None = None
    test_mode: bool = False


class StripePaymentsConfig(BasePaymentsConfig):
    """TODO: Payments configuration using Stripe."""

    type: Literal["stripe"] = "stripe"


class UgentPaymentsConfig(BasePaymentsConfig):
    """Payments configuration using UGent bridge."""

    type: Literal["ugent"] = "ugent"
    wbs_element: str
    ingenico_salt: str
    allow_invoices: bool = True


PaymentsConfig = UgentPaymentsConfig | StripePaymentsConfig | None
