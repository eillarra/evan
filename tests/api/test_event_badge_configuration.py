from http import HTTPStatus as status

import pytest

from tests._factories import UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
class TestEventBadgeConfiguration:
    """Test badge configuration through the event API endpoint."""

    def test_update_badges_configuration(self, api_client, t_event, t_event_manager) -> None:
        """Test updating badge configuration via PATCH to event endpoint."""
        from evan.models import Fee

        api_client.force_authenticate(user=t_event_manager)

        # Create fees FIRST before setting badge config
        Fee.objects.create(event=t_event, type="student", value=50)
        Fee.objects.create(event=t_event, type="faculty", value=100)

        badge_config = {
            "default": "#2563eb",
            "guest": "#059669",
            "fee_colors": {"student": "#2ecc71", "faculty": "#f39c12"},
        }

        data = {"extra_data": {"badges": badge_config}}

        url = t_event.get_api_url()
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.OK

        t_event.refresh_from_db()
        badges_config = t_event.badges_configuration

        assert badges_config["default"] == "#2563eb"
        assert badges_config["guest"] == "#059669"
        assert badges_config["fee_colors"]["student"] == "#2ecc71"
        assert badges_config["fee_colors"]["faculty"] == "#f39c12"

    def test_badges_configuration_filtering(self, api_client, t_event, t_event_manager) -> None:
        """Test that invalid fee types are filtered when accessing badges_configuration."""
        from evan.models import Fee

        api_client.force_authenticate(user=t_event_manager)

        Fee.objects.create(
            event=t_event,
            type="student",
            early_value=50,
            value=75,
            notes="Student rate",
            config={"included_social_events": []},
        )
        Fee.objects.create(
            event=t_event,
            type="faculty",
            early_value=100,
            value=150,
            notes="Faculty rate",
            config={"included_social_events": []},
        )

        badge_config = {
            "default": "#2563eb",
            "guest": "#059669",
            "fee_colors": {
                "student": "#2ecc71",
                "faculty": "#f39c12",
                "invalid_fee": "#9b59b6",
            },
        }

        data = {"extra_data": {"badges": badge_config}}

        url = t_event.get_api_url()
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.OK

        t_event.refresh_from_db()
        filtered_config = t_event.badges_configuration

        print("Filtered badge configuration:", filtered_config)

        assert filtered_config["default"] == "#2563eb"
        assert filtered_config["guest"] == "#059669"

        assert "student" in filtered_config["fee_colors"]
        assert "faculty" in filtered_config["fee_colors"]
        assert "invalid_fee" not in filtered_config["fee_colors"]

        assert filtered_config["fee_colors"]["student"] == "#2ecc71"
        assert filtered_config["fee_colors"]["faculty"] == "#f39c12"

    def test_empty_badges_configuration(self, api_client, t_event, t_event_manager) -> None:
        """Test that badges_configuration returns defaults when not configured."""
        api_client.force_authenticate(user=t_event_manager)

        # Verify default configuration
        default_config = t_event.badges_configuration

        assert default_config["default"] == "#2563eb"  # Default blue
        assert default_config["guest"] == "#059669"  # Default green
        assert default_config["fee_colors"] == {}  # Empty by default
        assert default_config["sort_by"] == "first_name"  # Default sort
        assert default_config["group_by"] == "none"  # Default group

    def test_update_badges_configuration_with_sort_and_group(self, api_client, t_event, t_event_manager) -> None:
        """Test updating badge configuration with sort_by and group_by options."""
        from evan.models import Fee

        api_client.force_authenticate(user=t_event_manager)

        # Create fees
        Fee.objects.create(event=t_event, type="student", value=50)
        Fee.objects.create(event=t_event, type="faculty", value=100)

        badge_config = {
            "default": "#2563eb",
            "guest": "#059669",
            "fee_colors": {"student": "#2ecc71", "faculty": "#f39c12"},
            "sort_by": "last_name",
            "group_by": "fee",
        }

        data = {"extra_data": {"badges": badge_config}}

        url = t_event.get_api_url()
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.OK

        t_event.refresh_from_db()
        badges_config = t_event.badges_configuration

        assert badges_config["default"] == "#2563eb"
        assert badges_config["guest"] == "#059669"
        assert badges_config["fee_colors"]["student"] == "#2ecc71"
        assert badges_config["fee_colors"]["faculty"] == "#f39c12"
        assert badges_config["sort_by"] == "last_name"
        assert badges_config["group_by"] == "fee"
