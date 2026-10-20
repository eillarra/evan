"""Behavior tests for the user API: profile updates and the user search."""

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


@pytest.mark.api
@pytest.mark.django_db
class TestUserSearch:
    """The user search, open to event managers, lists users whatever profile fields they have filled in."""

    @pytest.mark.parametrize("country", ["", "BE"])
    def test_country_is_rendered_as_a_plain_code(self, api_client, t_event_manager, country) -> None:
        UserFactory(first_name="Zed", last_name="Searchable", country=country)
        api_client.force_authenticate(user=t_event_manager)

        response = api_client.get(reverse("v1:search_users-list"), {"search": "Searchable"})

        assert response.status_code == status.OK
        assert [row["country"] for row in response.json()["results"]] == [country]
