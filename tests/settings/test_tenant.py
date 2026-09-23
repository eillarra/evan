import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings


BASE_IMPORT = "import evan.settings.base"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _import_base_with_tenant(tenant: str | None) -> subprocess.CompletedProcess[str]:
    """Import the base settings module in a subprocess with a controlled tenant variable.

    :param tenant: The UGENT_TENANT_ID value to expose (None removes it from the environment).
    :returns: The completed subprocess result.
    """
    env = {key: value for key, value in os.environ.items() if key != "UGENT_TENANT_ID"}
    if tenant is not None:
        env["UGENT_TENANT_ID"] = tenant
    return subprocess.run(
        [sys.executable, "-c", BASE_IMPORT],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )


@pytest.mark.parametrize("tenant", [None, "", "   ", "organizations", "common", "consumers", "ORGANIZATIONS"])
def test_base_settings_fail_fast_without_pinned_tenant(tenant):
    """Boot without a pinned UGent tenant fails with an explicit configuration error."""
    result = _import_base_with_tenant(tenant)

    assert result.returncode != 0
    assert "UGENT_TENANT_ID must be set to the UGent Microsoft tenant id" in result.stderr


def test_base_settings_import_with_pinned_tenant():
    """Boot with a concrete tenant id imports cleanly."""
    result = _import_base_with_tenant("d61d60ab-9c92-43b5-a7e3-0f2b4d1c6c3f")

    assert result.returncode == 0, result.stderr


def test_account_email_verification_is_none():
    """Sign-up never requires an e-mail verification step."""
    assert settings.ACCOUNT_EMAIL_VERIFICATION == "none"


def test_social_provider_apps_installed():
    """All four social login providers are installed."""
    expected_providers = {
        "allauth.socialaccount.providers.github",
        "allauth.socialaccount.providers.google",
        "allauth.socialaccount.providers.linkedin_oauth2",
        "evan.ugent_provider",
    }
    assert expected_providers <= set(settings.INSTALLED_APPS)


def test_ugent_provider_tenant_is_pinned():
    """The configured tenant is never a permissive wildcard, whatever the environment."""
    tenant = settings.SOCIALACCOUNT_PROVIDERS["ugent"]["TENANT"]

    assert tenant
    assert tenant not in {"organizations", "common", "consumers"}
