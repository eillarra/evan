from http import HTTPStatus as status

import pytest

from evan.utils.factories import CouponFactory, EventFactory, RegistrationFactory, UserFactory


@pytest.fixture
def coupon(db, test_event):
    return CouponFactory(event=test_event)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
class TestForAnonymous:
    expected_status_codes: dict[str, status] = {
        "list": status.FORBIDDEN,
        "create": status.FORBIDDEN,
        "update": status.FORBIDDEN,
    }

    def _get_endpoint(self, event) -> str:
        return event.get_api_url() + "coupons/"

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
            assert response.data["notes"] == data["notes"].strip()

    def test_update(self, api_client, coupon) -> None:
        data = self._get_update_data()
        response = api_client.put(coupon.get_api_url(), data)
        assert response.status_code == self.expected_status_codes["update"]


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)


class TestForEventManager(TestForAuthenticated):
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
            "value": 200,
            "notes": "Test coupon",
        }

    def _get_update_data(self):
        return {
            "value": 100,
            "notes": "  Test coupon (edited)",
        }

    def _get_invalid_data(self):
        return {
            "notes": "Updated notes",
        }

    def test_create_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        url = self._get_endpoint(other_event)
        response = api_client.post(url, self._get_create_data())
        assert response.status_code == status.FORBIDDEN

    def test_update_for_other_event(self, api_client) -> None:
        other_event = EventFactory()
        other_coupon = CouponFactory(event=other_event)
        response = api_client.put(other_coupon.get_api_url(), self._get_update_data())
        assert response.status_code == status.FORBIDDEN

    def test_delete(self, api_client, coupon) -> None:
        response = api_client.delete(coupon.get_api_url())
        assert response.status_code == self.expected_status_codes["delete"]

    def test_delete_used_coupon(self, api_client, coupon) -> None:
        RegistrationFactory(event=coupon.event, coupon=coupon, user=UserFactory())
        response = api_client.delete(coupon.get_api_url())
        assert response.status_code == status.FORBIDDEN
