"""Smoke tests for allauth account templates.

Regression coverage for EVAN-BACKEND-4W: ``account/email.html``,
``account/email_confirm.html`` and ``account/password_change.html`` extended
a non-existent ``users/base.html`` and raised ``TemplateDoesNotExist`` on
every render. These tests hit each URL and assert a successful render
instead of a 500.
"""

from http import HTTPStatus as status

import pytest
from django.urls import reverse

from tests._factories import UserFactory


@pytest.fixture
def user(db):
    """A regular authenticated user."""
    return UserFactory()


@pytest.mark.site
@pytest.mark.django_db
class TestForAnonymous:
    """Anonymous users are redirected to the login page by allauth."""

    expected_status_codes: dict[str, status] = {
        "email": status.FOUND,
        "password_change": status.FOUND,
        "email_confirm_invalid_key": status.OK,
    }

    def test_email_management_redirects(self, client):
        response = client.get(reverse("account_email"))
        assert response.status_code == self.expected_status_codes["email"]

    def test_password_change_redirects(self, client):
        response = client.get(reverse("account_change_password"))
        assert response.status_code == self.expected_status_codes["password_change"]

    def test_email_confirm_invalid_key_renders(self, client):
        # Renders the "expired/invalid" branch, which still requires the base
        # template chain to resolve -- the exact 4W failure mode.
        response = client.get(reverse("account_confirm_email", args=["invalid-key"]))
        assert response.status_code == self.expected_status_codes["email_confirm_invalid_key"]


class TestForAuthenticated(TestForAnonymous):
    """Authenticated users get a 200 render on account management pages."""

    expected_status_codes: dict[str, status] = {
        "email": status.OK,
        "password_change": status.OK,
        "email_confirm_invalid_key": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, client, user):
        client.force_login(user=user)
