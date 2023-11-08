from http import HTTPStatus as status

import pytest

from evan.utils.factories import EventFactory, SessionFactory, UserFactory


@pytest.fixture
def session(db, test_event):
    return SessionFactory(event=test_event)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
class TestForAnonymous:
    sees_secrets = False
    expected_status_codes: dict[str, status] = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.FORBIDDEN,
        "update": status.FORBIDDEN,
    }

    def _get_endpoint(self, event) -> str:
        return event.get_api_url() + "sessions/"

    def _get_create_data(self):
        return {}

    def _get_update_data(self):
        return {}

    def test_list(self, api_client, test_event) -> None:
        url = self._get_endpoint(test_event)
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list"]

    def test_retrieve(self, api_client, session) -> None:
        response = api_client.get(session.get_api_url())
        assert response.status_code == self.expected_status_codes["retrieve"]
        assert ("uuid" in response.data) is self.sees_secrets
        assert ("secret_url" in response.data) is self.sees_secrets

    def test_create(self, api_client, test_event) -> None:
        url = self._get_endpoint(test_event)
        data = self._get_create_data()
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]

        if response.status_code == status.CREATED:
            assert response.data["title"] == data["title"].strip()

    def test_update(self, api_client, session) -> None:
        data = self._get_update_data()
        response = api_client.put(session.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestForUserWithEditLink(TestForAnonymous):
    expected_status_codes = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.FORBIDDEN,
        "update": status.OK,
    }

    def _get_update_data(self):
        return {
            "title": "Updated title",
        }

    def test_update(self, api_client, session) -> None:
        # This user uses an X-Evan-Secret header that allows them to edit the session
        api_client.credentials(HTTP_X_EVAN_SECRET=session.secret)
        data = self._get_update_data()
        response = api_client.put(session.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]


class TestForEventManager(TestForAuthenticated):
    sees_secrets = True
    expected_status_codes = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.CREATED,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, test_event_manager):
        api_client.force_authenticate(user=test_event_manager)

    def _get_create_data(self):
        return {
            "title": "Session title",
            "description": "Session description",
        }

    def _get_update_data(self):
        return {
            "title": "Updated title",
            "description": "Updated description",
        }

    def test_create_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        url = self._get_endpoint(other_event)
        response = api_client.post(url, self._get_create_data())
        assert response.status_code == status.FORBIDDEN

    def test_update_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        other_content = SessionFactory(event=other_event)
        response = api_client.put(other_content.get_api_url(), self._get_update_data())
        assert response.status_code == status.FORBIDDEN

    def test_delete(self, api_client, session) -> None:
        response = api_client.delete(session.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]
