"""Unit tests for the Worldline payment service.

Covers deterministic ORDERID generation, SHA-512 parameter hashing, the SHA-OUT
tamper-detection callback, process_parameters composition, and endpoint selection.
These are pure crypto / configuration boundaries — no DB, no network.
"""

from hashlib import sha512
from unittest.mock import patch

import pytest
from django.http import QueryDict

from evan.services.payments.ugent_bridge import SHA_OUT_PARAMS, UGentBridge


# ---------------------------------------------------------------------------
# Known SHASIGN vector (provided by Ingenico/Ogone documentation)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query_string,salt",
    [
        (
            "AAVADDRESS=NO&AAVCHECK=KO&AAVZIP=KO&ACCEPTANCE=067891&AMOUNT=150&BIN=471532&BRAND=VISA&CARDNO=XXXXXXXXXXXX5594&CCCTY=GB&CN=Evan&CREDITDEBIT=&CURRENCY=EUR&CVCCHECK=OK&ECI=5&ED=0422&IPCTY=GB&NCERROR=0&ORDERID=1365/1599730668&PAYID=5451031176&PM=CreditCard&SHASIGN=E0B1DC00DB95CA8FDA14EBD7D877979709C980DE21C10BADB49D404C009FBA8E2F4BDB779B07E6331B6A691792CD155D4A50FFE55F17408C3C8B0E2B09EF59F3&STATUS=9&SUBBRAND=Visa Purchasing&TRXDATE=09/10/20&VC=NO",  # noqa: E501
            "ogonehash",
        )
    ],
)
def test_valid_query_parameters(query_string, salt):
    assert UGentBridge.validate_out_parameters(QueryDict(query_string), outsalt=salt)


# ---------------------------------------------------------------------------
# generate_order_id
# ---------------------------------------------------------------------------


class TestGenerateOrderId:
    """The external ORDERID is deterministic and rotates on amount or extra_hash changes."""

    def test_deterministic_for_same_inputs(self) -> None:
        assert UGentBridge.generate_order_id(42, 100) == UGentBridge.generate_order_id(42, 100)

    def test_changes_when_amount_changes(self) -> None:
        assert UGentBridge.generate_order_id(42, 100) != UGentBridge.generate_order_id(42, 200)

    def test_changes_when_extra_hash_added(self) -> None:
        without = UGentBridge.generate_order_id(42, 100)
        with_hash = UGentBridge.generate_order_id(42, 100, extra_hash="abc12345")
        assert without != with_hash

    def test_changes_when_extra_hash_changes(self) -> None:
        assert UGentBridge.generate_order_id(42, 100, extra_hash="aaa") != UGentBridge.generate_order_id(
            42, 100, extra_hash="bbb"
        )

    def test_format_is_base_dash_8_hex(self) -> None:
        order_id = UGentBridge.generate_order_id(42, 100)
        base, _, suffix = order_id.partition("-")
        assert base == "42"
        assert len(suffix) == 8
        int(suffix, 16)  # raises if not hex


# ---------------------------------------------------------------------------
# hash_parameters
# ---------------------------------------------------------------------------


class TestHashParameters:
    """hash_parameters concatenates sorted KEY=VALUEsalt pairs and SHA-512s them."""

    def test_matches_independently_computed_sha512(self) -> None:
        worldline = UGentBridge(pspid="PSP", salt="S4LT")
        params = {"ORDERID": "42", "AMOUNT": "100", "CURRENCY": "EUR"}

        expected_string = "".join(f"{k}={params[k]}S4LT" for k in sorted(params))
        expected = sha512(expected_string.encode("utf-8")).hexdigest().upper()

        assert worldline.hash_parameters(params) == expected

    def test_different_salt_produces_different_hash(self) -> None:
        params = {"ORDERID": "42", "AMOUNT": "100"}
        a = UGentBridge(pspid="PSP", salt="salt-a").hash_parameters(params)
        b = UGentBridge(pspid="PSP", salt="salt-b").hash_parameters(params)
        assert a != b

    def test_empty_parameters_hashes_salt_only(self) -> None:
        worldline = UGentBridge(pspid="PSP", salt="onlysalt")
        expected = sha512(b"").hexdigest().upper()
        assert worldline.hash_parameters({}) == expected


# ---------------------------------------------------------------------------
# validate_out_parameters
# ---------------------------------------------------------------------------


def _build_valid_callback(outsalt: str, **overrides) -> QueryDict:
    """Build a SHA-OUT callback querystring carrying a valid SHASIGN for the given salt.

    :param outsalt: The SHA-OUT salt used to sign the parameters.
    :param overrides: Parameter overrides applied before signing.
    :returns: A QueryDict whose SHASIGN matches the remaining parameters.
    """
    params = {"ORDERID": "42", "AMOUNT": "100", "STATUS": "9", "PAYID": "5451031176", "CURRENCY": "EUR"}
    params.update(overrides)

    string_to_hash = ""
    for key in sorted(params):
        ku = key.upper()
        if ku in SHA_OUT_PARAMS and params[key]:
            string_to_hash += f"{ku}={params[key]}{outsalt}"

    shasign = sha512(string_to_hash.encode("utf-8")).hexdigest().upper()

    qs = QueryDict(mutable=True)
    for key, value in params.items():
        qs[key] = value
    qs["SHASIGN"] = shasign
    return qs


class TestValidateOutParameters:
    """validate_out_parameters accepts a genuine SHASIGN and rejects tampered or missing ones."""

    def test_valid_signature_is_accepted(self) -> None:
        qs = _build_valid_callback(outsalt="outsalt")
        assert UGentBridge.validate_out_parameters(qs, outsalt="outsalt") is True

    def test_tampered_amount_is_rejected(self) -> None:
        qs = _build_valid_callback(outsalt="outsalt")
        qs["AMOUNT"] = "999"  # tamper after signing
        assert UGentBridge.validate_out_parameters(qs, outsalt="outsalt") is False

    def test_missing_shasign_is_rejected(self) -> None:
        qs = _build_valid_callback(outsalt="outsalt")
        qs.pop("SHASIGN")
        assert UGentBridge.validate_out_parameters(qs, outsalt="outsalt") is False

    def test_unknown_parameters_are_ignored(self) -> None:
        qs = _build_valid_callback(outsalt="outsalt", UNKNOWN="noise")
        assert UGentBridge.validate_out_parameters(qs, outsalt="outsalt") is True

    def test_lowercase_parameter_names_are_normalised(self) -> None:
        qs = _build_valid_callback(outsalt="outsalt")
        lowercase = QueryDict(mutable=True)
        for key, value in qs.lists():
            lowercase[key.lower()] = value[0]
        lowercase["SHASIGN"] = qs["SHASIGN"]
        assert UGentBridge.validate_out_parameters(lowercase, outsalt="outsalt") is True


# ---------------------------------------------------------------------------
# process_parameters
# ---------------------------------------------------------------------------


class TestProcessParameters:
    """process_parameters composes the Worldline form payload with a signed SHASIGN."""

    def test_output_contains_required_keys(self) -> None:
        worldline = UGentBridge(pspid="TESTPSP", salt="salt", test_mode=True)
        user = type("FakeUser", (), {"email": "attendee@example.com"})()
        params = {"ORDERID": 42, "AMOUNT": 100, "RESULTURL": "/result", "CALLBACKURL": "/callback"}

        with patch("evan.services.payments.ugent_bridge.get_absolute_uri", return_value="https://test.example.com"):
            result = worldline.process_parameters(params, user, extra_hash="abc12345")

        assert result["PSPID"] == "TESTPSP"
        assert result["AMOUNT"] == 10000  # EUR → cents
        assert result["EMAIL"] == "attendee@example.com"
        assert result["ORDERID"].startswith("42-")
        assert "SHASIGN" in result
        for key in ("ACCEPTURL", "DECLINEURL", "CANCELURL", "EXCEPTIONURL", "BACKURL"):
            assert key in result
            assert result[key].startswith("https://test.example.com")

    def test_exceptionurl_points_to_the_same_result_page_as_accepturl(self) -> None:
        """Without an explicit EXCEPTIONURL, Worldline falls back to a static back-office
        default instead of the registration's own result page for STATUS 52/92."""
        worldline = UGentBridge(pspid="TESTPSP", salt="salt", test_mode=True)
        user = type("FakeUser", (), {"email": "attendee@example.com"})()
        params = {"ORDERID": 42, "AMOUNT": 100, "RESULTURL": "/result", "CALLBACKURL": "/callback"}

        with patch("evan.services.payments.ugent_bridge.get_absolute_uri", return_value="https://test.example.com"):
            result = worldline.process_parameters(params, user, extra_hash="abc12345")

        assert result["EXCEPTIONURL"] == result["ACCEPTURL"]

    def test_orderid_is_deterministic_form(self) -> None:
        worldline = UGentBridge(pspid="TESTPSP", salt="salt", test_mode=True)
        user = type("FakeUser", (), {"email": "attendee@example.com"})()
        params = {"ORDERID": 42, "AMOUNT": 100, "RESULTURL": "/result", "CALLBACKURL": "/callback"}

        with patch("evan.services.payments.ugent_bridge.get_absolute_uri", return_value="https://test.example.com"):
            first = worldline.process_parameters(params, user, extra_hash="abc12345")
            second = worldline.process_parameters(params, user, extra_hash="abc12345")

        assert first["ORDERID"] == second["ORDERID"]


# ---------------------------------------------------------------------------
# get_url
# ---------------------------------------------------------------------------


class TestGetUrl:
    """get_url returns the test or production endpoint based on test_mode."""

    def test_test_mode_returns_test_url(self) -> None:
        worldline = UGentBridge(pspid="PSP", salt="salt", test_mode=True)
        worldline.TEST_URL = "https://test.worldline.example"
        worldline.PRODUCTION_URL = "https://prod.worldline.example"
        assert worldline.get_url() == "https://test.worldline.example"

    def test_production_mode_returns_production_url(self) -> None:
        worldline = UGentBridge(pspid="PSP", salt="salt", test_mode=False)
        worldline.TEST_URL = "https://test.worldline.example"
        worldline.PRODUCTION_URL = "https://prod.worldline.example"
        assert worldline.get_url() == "https://prod.worldline.example"
