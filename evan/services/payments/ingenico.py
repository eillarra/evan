import hmac
import os
from hashlib import sha512
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import QueryDict


if TYPE_CHECKING:
    from evan.models.users import User


# https://shared.ecom-psp.com/v2/docs/guides/e-Commerce/SHA-OUT_params.txt
SHA_OUT_PARAMS: frozenset[str] = frozenset(
    {
        "AAVADDRESS",
        "AAVCHECK",
        "AAVMAIL",
        "AAVNAME",
        "AAVPHONE",
        "AAVZIP",
        "ACCEPTANCE",
        "ALIAS",
        "AMOUNT",
        "BIC",
        "BIN",
        "BRAND",
        "CARDNO",
        "CCCTY",
        "CN",
        "COLLECTOR_BIC",
        "COLLECTOR_IBAN",
        "COMPLUS",
        "CREATION_STATUS",
        "CREDITDEBIT",
        "CURRENCY",
        "CVCCHECK",
        "DCC_COMMPERCENTAGE",
        "DCC_CONVAMOUNT",
        "DCC_CONVCCY",
        "DCC_EXCHRATE",
        "DCC_EXCHRATESOURCE",
        "DCC_EXCHRATETS",
        "DCC_INDICATOR",
        "DCC_MARGINPERCENTAGE",
        "DCC_VALIDHOURS",
        "DEVICEID",
        "DIGESTCARDNO",
        "ECI",
        "ED",
        "EMAIL",
        "ENCCARDNO",
        "FXAMOUNT",
        "FXCURRENCY",
        "IP",
        "IPCTY",
        "MANDATEID",
        "MOBILEMODE",
        "NBREMAILUSAGE",
        "NBRIPUSAGE",
        "NBRIPUSAGE_ALLTX",
        "NBRUSAGE",
        "NCERROR",
        "ORDERID",
        "PAYID",
        "PAYIDSUB",
        "PAYMENT_REFERENCE",
        "PM",
        "SCO_CATEGORY",
        "SCORING",
        "SEQUENCETYPE",
        "SIGNDATE",
        "STATUS",
        "SUBBRAND",
        "SUBSCRIPTION_ID",
        "TICKET",
        "TRXDATE",
        "VC",
    }
)


def get_absolute_uri():
    """Return the site absolute base URL used in payment callbacks.

    :returns: The current site domain prefixed with the active protocol.
    """
    protocol = "https://" if settings.SESSION_COOKIE_SECURE else "http://"
    return protocol + Site.objects.get_current().domain


class Ingenico:
    PRODUCTION_URL = os.environ.get("INGENICO_PRODUCTION_URL")
    TEST_URL = os.environ.get("INGENICO_TEST_URL")
    SUCCESS_STATUSES = {"5", "51", "9", "91"}
    EXCEPTION_STATUSES = {"52", "92"}
    DECLINE_STATUSES = {"2"}
    CANCEL_STATUSES = {"1"}
    INVALID_STATUSES = {"0"}

    def __init__(self, *, pspid: str = "", salt: str = "", test_mode: bool = True):
        self.pspid = pspid
        self.salt = salt
        self.test_mode = test_mode

    def get_url(self):
        """Return the configured Ingenico endpoint URL.

        :returns: The test or production endpoint depending on configuration.
        """
        return self.TEST_URL if self.test_mode else self.PRODUCTION_URL

    @staticmethod
    def generate_order_id(base_order_id: str | int, amount: int, extra_hash: str | None = None) -> str:
        """Generate the deterministic ORDERID sent to Ingenico.

        :param base_order_id: The internal registration identifier.
        :param amount: The expected payment amount in EUR.
        :param extra_hash: Optional unique hash used to rotate payment attempts.
        :returns: The deterministic external ORDERID.
        """
        base_string = f"{base_order_id}-{amount}"
        if extra_hash:
            base_string += f"-{extra_hash}"
        short_hash = sha512(base_string.encode()).hexdigest()[:8]
        return f"{base_order_id}-{short_hash}"

    def hash_parameters(self, parameters: dict) -> str:
        """Generate SHA-512 hash with sorted parameters."""
        string_to_hash = ""

        for key in sorted(parameters):
            string_to_hash += key + "=" + str(parameters[key]) + self.salt

        return sha512(string_to_hash.encode("utf-8")).hexdigest().upper()

    def process_parameters(
        self, parameters: dict, user: User, extra_hash: str | None = None, *, paramvar: str | None = None
    ) -> dict:
        """Process and check if a minimum of parameters have been received.

        :param paramvar: Optional value submitted as Ingenico's ``PARAMVAR`` field.
            Ingenico substitutes it into the ``<PARAMVAR>`` placeholder of the
            account's configured "Direct HTTP server-to-server request" URL,
            letting that account-wide feedback URL resolve to a per-registration
            path (see ``RegistrationPaymentCallbackView``).
        """
        ingenico_parameters = {
            "CURRENCY": "EUR",
            "LANGUAGE": "en_US",
            "BGCOLOR": "#f5f5f5",
            "TXTCOLOR": "#222",
        }

        # User parameters
        ingenico_parameters.update({"EMAIL": user.email})

        # Required parameters
        absolute_uri = get_absolute_uri()

        order_id = self.generate_order_id(parameters["ORDERID"], parameters["AMOUNT"], extra_hash)

        ingenico_parameters.update(
            {
                "PSPID": self.pspid,
                "ORDERID": order_id,
                "AMOUNT": parameters["AMOUNT"] * 100,
                "COM": "ID" + str(parameters["ORDERID"]),
                "ACCEPTURL": absolute_uri + parameters["RESULTURL"],
                "DECLINEURL": absolute_uri + parameters["RESULTURL"],
                "CANCELURL": absolute_uri + parameters["RESULTURL"],
                "EXCEPTIONURL": absolute_uri + parameters["RESULTURL"],
                "BACKURL": absolute_uri + parameters["CALLBACKURL"],
            }
        )
        if paramvar:
            ingenico_parameters["PARAMVAR"] = paramvar

        ingenico_parameters.update({"SHASIGN": self.hash_parameters(ingenico_parameters)})

        return ingenico_parameters

    @classmethod
    def validate_out_parameters(cls, query_params: QueryDict, *, outsalt: str) -> bool:
        """Check if the URL parameters have been tampered."""

        parameters = query_params.dict()
        shasign = parameters.pop("SHASIGN", None)

        string_to_hash = ""

        for key in sorted(parameters):
            ku = key.upper()
            if ku in SHA_OUT_PARAMS and parameters[key]:
                string_to_hash += f"{ku}={parameters[key]}{outsalt}"

        expected = sha512(string_to_hash.encode("utf-8")).hexdigest().upper()
        return hmac.compare_digest(shasign or "", expected)
