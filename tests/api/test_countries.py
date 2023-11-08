from http import HTTPStatus as status

import pytest

from evan.utils.factories import UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
class TestForAnonymous:
    def test_list(self, api_client) -> None:
        response = api_client.get("/api/countries/")
        assert response.status_code == status.OK
        assert "BE" in response.data


class TestForAuthenticated(TestForAnonymous):
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user):
        api_client.force_authenticate(user=user)
