from http import HTTPStatus as status

import pytest

from evan.utils.factories import ContentFactory, EventFactory, UserFactory


@pytest.fixture
def content(db, test_event):
    return ContentFactory(event=test_event)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
class TestForAnonymous:
    expected_status_codes: dict[str, status] = {
        "list": status.OK,
        "create": status.FORBIDDEN,
        "update": status.FORBIDDEN,
    }

    def _get_endpoint(self, event) -> str:
        return event.get_api_url() + "contents/"

    def _get_create_data(self):
        return {}

    def _get_update_data(self):
        return {}

    def test_list(self, api_client, test_event) -> None:
        url = self._get_endpoint(test_event)
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list"]

    def test_create(self, api_client, test_event) -> None:
        url = self._get_endpoint(test_event)
        data = self._get_create_data()
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]

        if response.status_code == status.CREATED:
            assert response.data["value"] == data["value"].strip()

    def test_update(self, api_client, content) -> None:
        data = self._get_update_data()
        response = api_client.put(content.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestForEventManager(TestForAuthenticated):
    expected_status_codes = {
        "list": status.OK,
        "create": status.CREATED,
        "update": status.OK,
        "delete": status.FORBIDDEN,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, test_event_manager):
        api_client.force_authenticate(user=test_event_manager)

    def _get_create_data(self):
        return {
            "key": "new_key",
            "value": "New content",
        }

    def _get_update_data(self):
        return {
            "key": "new_key",
            "value": "  New content. Multiline: \n 1. First line\n 2. Second line",
        }

    def test_create_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        url = self._get_endpoint(other_event)
        response = api_client.post(url, self._get_create_data())
        assert response.status_code == status.FORBIDDEN

    def test_update_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        other_content = ContentFactory(event=other_event)
        response = api_client.put(other_content.get_api_url(), self._get_update_data())
        assert response.status_code == status.FORBIDDEN

    def test_update_key_should_be_ignored(self, api_client, content) -> None:
        response = api_client.put(content.get_api_url(), {"key": "updated_key"})
        assert response.status_code == status.OK
        assert response.data["key"] == content.key
        assert response.data["value"] == content.value

    def test_delete(self, api_client, content) -> None:
        response = api_client.delete(content.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]
