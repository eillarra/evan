"""Guards for settings whose value depends on how they are merged across environments."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.template import engines
from pytest_django.fixtures import Settings


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_ENGINE_CHECK = (
    "import django; django.setup(); from django.template import engines; print(engines['django'].engine.debug)"
)


@pytest.mark.parametrize("debug", [True, False])
def test_templates_engine_debug_follows_settings(debug: bool, settings: Settings) -> None:
    """The template engine reads ``debug`` from settings, not from a literal.

    Hard-coding it in ``TEMPLATES[0]["OPTIONS"]`` froze the value at import time:
    ``base.py`` is imported while ``DEBUG`` is still ``True``, and ``production.py``
    only turns it off afterwards, so the engine kept compiling templates with the
    debug lexer in production.
    """
    settings.DEBUG = debug

    assert engines["django"].engine.debug is debug


def test_production_template_engine_is_not_in_debug() -> None:
    """The merged production settings build a non-debug engine."""
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "evan.settings.production",
        "UGENT_TENANT_ID": "test-tenant",
    }
    result = subprocess.run(
        [sys.executable, "-c", PRODUCTION_ENGINE_CHECK],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"
