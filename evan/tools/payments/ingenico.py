import os
import time
import unicodedata

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import QueryDict
from hashlib import sha512


def get_absolute_uri():
    protocol = "https://" if settings.SESSION_COOKIE_SECURE else "http://"
    return protocol + Site.objects.get_current().domain


class Ingenico:
    PRODUCTION_URL = os.environ.get("INGENICO_PRODUCTION_URL")
    TEST_URL = os.environ.get("INGENICO_TEST_URL")
    SUCCESS_STATUSES = ("5", "51", "9", "91")
    EXCEPTION_STATUSES = ("52", "92")
    DECLINE_STATUSES = ("2",)
    CANCEL_STATUSES = ("1",)
    INVALID_STATUSES = ("0",)

    def __init__(self, *, pspid: str = "", salt: str = "", test_mode: bool = True):
        self.pspid = pspid
        self.salt = salt
        self.test_mode = test_mode

    def get_url(self):
        return self.TEST_URL if self.test_mode else self.PRODUCTION_URL

    def hash_parameters(self, parameters: dict) -> str:
        """Generate SHA1 with sorted parameters."""
        string_to_hash = ""

        for key in sorted(parameters):
            string_to_hash += key + "=" + str(parameters[key]) + self.salt

        return sha512(string_to_hash.encode("utf-8")).hexdigest().upper()

    def process_parameters(self, parameters: dict, user) -> dict:
        """Process and check if a minimum of parameters have been received.
        """
        ingenico_parameters = {
            "CURRENCY": "EUR",
            "LANGUAGE": "en_US",
            "BGCOLOR": "#f5f5f5",
            "TXTCOLOR": "#222",
        }

        # User parameters
        ingenico_parameters.update(
            {
                "EMAIL": user.email,
                "CN": unicodedata.normalize("NFKD", user.profile.name)
                .encode("ascii", "ignore")
                .decode("utf-8")
                .upper(),
            }
        )

        # Required parameters
        absolute_uri = get_absolute_uri()
        ingenico_parameters.update(
            {
                "PSPID": self.pspid,
                "ORDERID": str(parameters["ORDERID"]) + "/" + str(int(time.time())),
                "AMOUNT": parameters["AMOUNT"] * 100,
                "COM": "ID" + str(parameters["ORDERID"]),
                "ACCEPTURL": absolute_uri + parameters["RESULTURL"],
                "DECLINEURL": absolute_uri + parameters["RESULTURL"],
            }
        )

        ingenico_parameters.update({"SHASIGN": self.hash_parameters(ingenico_parameters)})

        return ingenico_parameters

    def validate_query_parameters(self, query_parameters: QueryDict) -> None:
        """Check if the URL parameters have been tampered.
        """
        parameters = query_parameters.dict()
        shasign = parameters.pop("SHASIGN", None)
        return self.hash_parameters(parameters) == shasign
