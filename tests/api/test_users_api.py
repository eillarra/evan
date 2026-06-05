"""Behavior tests for user profile API updates."""

from http import HTTPStatus as status

import pytest
from django.urls import reverse

from tests._factories import UserFactory


@pytest.mark.api
@pytest.mark.django_db
class TestUserProfileUpdate:
    """Boundary tests for user profile patch operations."""

    def test_patch_with_null_country_returns_validation_error(self, api_client) -> None:
        """Sending an explicit null country should fail with 400 instead of crashing with 500."""
        user = UserFactory(country="BE")
        api_client.force_authenticate(user=user)

        response = api_client.patch(
            reverse("v1:user-detail", kwargs={"pk": user.pk}),
            {"country": None},
            format="json",
        )

        assert response.status_code == status.BAD_REQUEST
        assert "country" in response.data
