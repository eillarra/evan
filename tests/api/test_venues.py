from http import HTTPStatus as status

import pytest

from tests._factories import EventFactory, RoomFactory, UserFactory, VenueFactory


@pytest.fixture
def venue(db, t_event):
    """Create a venue for testing."""
    return VenueFactory(event=t_event)


@pytest.fixture
def room(db, venue):
    """Create a room for testing."""
    return RoomFactory(venue=venue)


@pytest.fixture
def user(db):
    """Create a user for testing."""
    return UserFactory()


@pytest.mark.api
class TestVenuesForAnonymous:
    """Test venue endpoints for anonymous users."""

    expected_status_codes: dict[str, status] = {
        "list": status.FORBIDDEN,
        "create": status.FORBIDDEN,
        "update": status.FORBIDDEN,
        "delete": status.FORBIDDEN,
    }

    def _get_endpoint(self, event) -> str:
        return event.get_api_url() + "venues/"

    def _get_create_data(self):
        return {
            "name": "Test Venue",
            "city": "Test City",
            "is_main": False,
        }

    def _get_update_data(self):
        return {
            "name": "Updated Venue",
            "city": "Updated City",
            "is_main": True,
        }

    def test_list(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list"]

    def test_create(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        data = self._get_create_data()
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]

    def test_update(self, api_client, venue) -> None:
        data = self._get_update_data()
        response = api_client.put(venue.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]

    def test_delete(self, api_client, venue) -> None:
        response = api_client.delete(venue.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]


class TestVenuesForAuthenticated(TestVenuesForAnonymous):
    """Test venue endpoints for authenticated users."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestVenuesForEventManager(TestVenuesForAuthenticated):
    """Test venue endpoints for event managers."""

    expected_status_codes = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.CREATED,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def _get_create_data(self):
        return {
            "name": "Test Venue",
            "city": "Test City",
            "is_main": False,
            "website": "https://example.com",
            "google_place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
        }

    def _get_update_data(self):
        return {
            "name": "Updated Venue",
            "city": "Updated City",
            "is_main": True,
            "website": "https://updated.com",
            "google_place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
        }

    def test_create(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        data = self._get_create_data()
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]
        assert response.data["name"] == data["name"]
        assert response.data["city"] == data["city"]
        assert response.data["is_main"] == data["is_main"]
        assert response.data["website"] == data["website"]
        assert response.data["google_place_id"] == data["google_place_id"]

    def test_update(self, api_client, venue) -> None:
        data = self._get_update_data()
        response = api_client.put(venue.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]
        assert response.data["name"] == data["name"]
        assert response.data["city"] == data["city"]
        assert response.data["is_main"] == data["is_main"]

    def test_create_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        url = self._get_endpoint(other_event)
        response = api_client.post(url, self._get_create_data())
        assert response.status_code == status.FORBIDDEN

    def test_update_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        other_venue = VenueFactory(event=other_event)
        response = api_client.put(other_venue.get_api_url(), self._get_update_data())
        assert response.status_code == status.FORBIDDEN

    def test_delete(self, api_client, venue) -> None:
        response = api_client.delete(venue.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]

    def test_main_venue_constraint(self, api_client, t_event) -> None:
        """Test that only one venue can be main at a time."""
        # Create first main venue
        url = self._get_endpoint(t_event)
        data1 = self._get_create_data()
        data1["is_main"] = True
        response1 = api_client.post(url, data1)
        assert response1.status_code == status.CREATED
        assert response1.data["is_main"] is True

        # Create second main venue - should succeed and make first non-main
        data2 = self._get_create_data()
        data2["name"] = "Second Venue"
        data2["is_main"] = True
        response2 = api_client.post(url, data2)
        assert response2.status_code == status.CREATED
        assert response2.data["is_main"] is True

        # Check that first venue is no longer main
        response1_check = api_client.get(response1.data["self"])
        assert response1_check.data["is_main"] is False


@pytest.mark.api
class TestRoomsForAnonymous:
    """Test room endpoints for anonymous users."""

    expected_status_codes: dict[str, status] = {
        "create": status.FORBIDDEN,
        "update": status.FORBIDDEN,
        "delete": status.FORBIDDEN,
    }

    def _get_endpoint(self, event) -> str:
        return event.get_api_url() + "rooms/"

    def _get_create_data(self, venue):
        return {
            "name": "Test Room",
            "max_capacity": 50,
            "position": 1,
            "venue": venue.id,
        }

    def _get_update_data(self):
        return {
            "name": "Updated Room",
            "max_capacity": 100,
            "position": 2,
        }

    def test_create(self, api_client, t_event, venue) -> None:
        url = self._get_endpoint(t_event)
        data = self._get_create_data(venue)
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]

    def test_update(self, api_client, room) -> None:
        data = self._get_update_data()
        response = api_client.put(room.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]

    def test_delete(self, api_client, room) -> None:
        response = api_client.delete(room.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]


class TestRoomsForAuthenticated(TestRoomsForAnonymous):
    """Test room endpoints for authenticated users."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestRoomsForEventManager(TestRoomsForAuthenticated):
    """Test room endpoints for event managers."""

    expected_status_codes = {
        "retrieve": status.OK,
        "create": status.CREATED,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def test_create(self, api_client, t_event, venue) -> None:
        url = self._get_endpoint(t_event)
        data = self._get_create_data(venue)
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]
        assert response.data["name"] == data["name"]
        assert response.data["max_capacity"] == data["max_capacity"]
        assert response.data["position"] == data["position"]
        assert "self" in response.data

    def test_update(self, api_client, room) -> None:
        data = self._get_update_data()
        response = api_client.put(room.get_api_url(), data)
        if response.status_code != self.expected_status_codes["update"]:
            print(f"Expected status: {self.expected_status_codes['update']}, got: {response.status_code}")
            print(f"Response data: {response.data}")
            print(f"Update data: {data}")
        assert response.status_code == self.expected_status_codes["update"]
        assert response.data["name"] == data["name"]
        assert response.data["max_capacity"] == data["max_capacity"]
        assert response.data["position"] == data["position"]

    def test_retrieve(self, api_client, room) -> None:
        response = api_client.get(room.get_api_url())
        assert response.status_code == self.expected_status_codes["retrieve"]
        assert response.data["id"] == room.id
        assert response.data["name"] == room.name
        assert "self" in response.data

    def test_delete(self, api_client, room) -> None:
        response = api_client.delete(room.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]

    def test_create_room_for_other_event_venue(self, api_client, t_event) -> None:
        """Test that creating a room for a venue in another event fails."""
        other_event = EventFactory()
        other_venue = VenueFactory(event=other_event)

        url = self._get_endpoint(t_event)
        data = self._get_create_data(other_venue)
        response = api_client.post(url, data)
        assert response.status_code == status.BAD_REQUEST

    def test_update_for_other_event(self, api_client) -> None:
        """Test that updating a room from another event fails."""
        other_event = EventFactory()
        other_venue = VenueFactory(event=other_event)
        other_room = RoomFactory(venue=other_venue)
        response = api_client.put(other_room.get_api_url(), self._get_update_data())
        assert response.status_code == status.FORBIDDEN
