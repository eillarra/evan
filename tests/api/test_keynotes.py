from http import HTTPStatus as status

import pytest

from tests._factories import EventFactory, KeynoteFactory, UserFactory


@pytest.fixture
def keynote(db, t_event):
    return KeynoteFactory(event=t_event)


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
        return event.get_api_url() + "keynotes/"

    def _get_create_data(self):
        return {}

    def _get_update_data(self):
        return {}

    def test_list(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list"]

    def test_retrieve(self, api_client, keynote) -> None:
        response = api_client.get(keynote.get_api_url())
        assert response.status_code == self.expected_status_codes["retrieve"]
        assert ("uuid" in response.data) is self.sees_secrets
        assert ("secret_url" in response.data) is self.sees_secrets

    def test_create(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        data = self._get_create_data()
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]

        if response.status_code == status.CREATED:
            assert response.data["title"] == data["title"].strip()

    def test_update(self, api_client, keynote) -> None:
        data = self._get_update_data()
        response = api_client.put(keynote.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]


@pytest.mark.api
class TestForEventManager(TestForAnonymous):
    sees_secrets = True
    expected_status_codes: dict[str, status] = {
        "list": status.OK,
        "retrieve": status.OK,
        "create": status.CREATED,
        "update": status.OK,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event_manager):
        api_client.force_authenticate(user=t_event_manager)

    def _get_create_data(self):
        return {
            "code": "TEST-K1",
            "title": "Test Keynote Title",
            "speaker": "Dr. Jane Doe",
            "bio": "Test speaker biography",
            "abstract": "Test keynote abstract",
        }

    def _get_update_data(self):
        return {
            "code": "UPDATED-K1",
            "title": "Updated Keynote Title",
            "speaker": "Dr. John Smith",
            "bio": "Updated speaker biography",
            "abstract": "Updated keynote abstract",
        }

    def test_create(self, api_client, t_event) -> None:
        url = self._get_endpoint(t_event)
        data = self._get_create_data()
        response = api_client.post(url, data)
        assert response.status_code == self.expected_status_codes["create"]
        assert response.data["title"] == data["title"]
        assert response.data["code"] == data["code"]
        assert response.data["speaker"] == data["speaker"]

    def test_update(self, api_client, keynote) -> None:
        data = self._get_update_data()
        response = api_client.put(keynote.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]
        assert response.data["title"] == data["title"]
        assert response.data["code"] == data["code"]
        assert response.data["speaker"] == data["speaker"]

    def test_list(self, api_client, t_event) -> None:
        keynote1 = KeynoteFactory(event=t_event, code="K1")
        keynote2 = KeynoteFactory(event=t_event, code="K2")
        other_event = EventFactory()
        KeynoteFactory(event=other_event, code="K3")

        url = self._get_endpoint(t_event)
        response = api_client.get(url)
        assert response.status_code == status.OK
        assert len(response.data) == 2

        codes = [keynote["code"] for keynote in response.data]
        assert keynote1.code in codes
        assert keynote2.code in codes

    def test_retrieve(self, api_client, keynote) -> None:
        response = api_client.get(keynote.get_api_url())
        assert response.status_code == self.expected_status_codes["retrieve"]
        assert response.data["code"] == keynote.code
        assert response.data["title"] == keynote.title
        assert ("uuid" in response.data) is self.sees_secrets
        assert ("secret_url" in response.data) is self.sees_secrets

    def test_update_for_other_event(self, api_client):
        other_event = EventFactory()
        other_keynote = KeynoteFactory(event=other_event)
        response = api_client.put(other_keynote.get_api_url(), self._get_update_data())
        assert response.status_code == status.FORBIDDEN
