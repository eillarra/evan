"""Remarks are private organizer notes: only managers of the registration's event may use them."""

from http import HTTPStatus as status

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.urls import reverse

from evan.models import Registration, User
from evan.models.rel.permissions import Permission
from evan.models.rel.remarks import Remark
from tests._factories import ContentFactory, EventFactory, RegistrationFactory, UserFactory


NOTE = "Original note"


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def registration(db, t_event) -> Registration:
    return RegistrationFactory(event=t_event, user=UserFactory())


@pytest.fixture
def remark(db, registration) -> Remark:
    return Remark.objects.create(content_object=registration, text=NOTE)


def parent_kwargs(obj: Model) -> dict[str, int]:
    return {
        "parent_lookup_content_type_id": ContentType.objects.get_for_model(obj).id,
        "parent_lookup_object_id": obj.pk,
    }


def list_url(obj: Model) -> str:
    return reverse("v1:remark-list", kwargs=parent_kwargs(obj))


def detail_url(obj: Model, remark: Remark) -> str:
    return reverse("v1:remark-detail", kwargs={**parent_kwargs(obj), "pk": remark.pk})


@pytest.fixture
def parents_without_remarks(t_event) -> dict[str, str]:
    """Remark URLs for parents that cannot carry remarks, however they are shaped."""
    sessions_table = ContentType.objects.get(app_label="sessions", model="session")
    removed_model = ContentType.objects.create(app_label="evan", model="removed")
    return {
        "event": list_url(t_event),
        "object with an event": list_url(ContentFactory(event=t_event)),
        "model without an id column": reverse(
            "v1:remark-list",
            kwargs={"parent_lookup_content_type_id": sessions_table.pk, "parent_lookup_object_id": 1},
        ),
        "removed model": reverse(
            "v1:remark-list",
            kwargs={"parent_lookup_content_type_id": removed_model.pk, "parent_lookup_object_id": 1},
        ),
    }


@pytest.mark.api
@pytest.mark.parametrize(
    "overrides",
    [
        {"parent_lookup_object_id": "0"},
        {"parent_lookup_object_id": "999999"},
        {"parent_lookup_object_id": "9" * 30},
        {"parent_lookup_object_id": "abc"},
        {"parent_lookup_content_type_id": 999999},
        {"parent_lookup_content_type_id": "9" * 30},
    ],
)
@pytest.mark.parametrize("who", ["user", "t_event_manager"])
def test_unknown_parent_is_refused(api_client, registration, request, who, overrides) -> None:
    api_client.force_authenticate(user=request.getfixturevalue(who))
    url = reverse("v1:remark-list", kwargs={**parent_kwargs(registration), **overrides})
    assert api_client.get(url).status_code == status.FORBIDDEN


@pytest.mark.api
@pytest.mark.parametrize("parent", ["event", "object with an event", "model without an id column", "removed model"])
@pytest.mark.parametrize("who", ["user", "t_event_manager"])
def test_parent_that_cannot_carry_remarks_is_refused(api_client, parents_without_remarks, request, who, parent) -> None:
    api_client.force_authenticate(user=request.getfixturevalue(who))
    assert api_client.get(parents_without_remarks[parent]).status_code == status.FORBIDDEN


@pytest.mark.api
def test_access_level_below_administrator_is_refused(api_client, t_event, registration, user) -> None:
    """Only administrator and owner rows grant access, so the level just below administrator grants nothing."""
    t_event.acl.create(user=user, level=Permission.ADMIN - 1)
    api_client.force_authenticate(user=user)

    assert api_client.get(list_url(registration)).status_code == status.FORBIDDEN


@pytest.mark.api
class TestForAnonymous:
    can_manage = False
    expected_status_codes: dict[str, status] = {
        "list": status.FORBIDDEN,
        "create": status.FORBIDDEN,
        "retrieve": status.FORBIDDEN,
        "update": status.FORBIDDEN,
        "delete": status.FORBIDDEN,
    }

    def test_list(self, api_client, registration, remark) -> None:
        response = api_client.get(list_url(registration))
        assert response.status_code == self.expected_status_codes["list"]
        assert (NOTE in response.content.decode()) is self.can_manage

    def test_create(self, api_client, registration) -> None:
        response = api_client.post(list_url(registration), {"text": "New note"}, format="json")
        assert response.status_code == self.expected_status_codes["create"]
        assert Remark.objects.filter(text="New note").exists() is self.can_manage

    def test_retrieve(self, api_client, registration, remark) -> None:
        response = api_client.get(detail_url(registration, remark))
        assert response.status_code == self.expected_status_codes["retrieve"]
        assert (NOTE in response.content.decode()) is self.can_manage

    def test_update(self, api_client, registration, remark) -> None:
        response = api_client.patch(detail_url(registration, remark), {"text": "Changed"}, format="json")
        assert response.status_code == self.expected_status_codes["update"]
        remark.refresh_from_db()
        assert remark.text == ("Changed" if self.can_manage else NOTE)

    def test_delete(self, api_client, registration, remark) -> None:
        response = api_client.delete(detail_url(registration, remark))
        assert response.status_code == self.expected_status_codes["delete"]
        was_deleted = not Remark.objects.filter(pk=remark.pk).exists()
        assert was_deleted is self.can_manage


class TestForAuthenticated(TestForAnonymous):
    """A signed-in user with no role on the event."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user) -> None:
        api_client.force_authenticate(user=user)


class TestForRegistrant(TestForAuthenticated):
    """Owning the registration does not grant access to the organizers' notes about it."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, registration) -> None:
        api_client.force_authenticate(user=registration.user)


class TestForOtherEventManager(TestForAuthenticated):
    """Managing a different event grants nothing here."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user) -> None:
        EventFactory().acl.create(user=user, level=Permission.ADMIN)
        api_client.force_authenticate(user=user)


class TestForEventGuest(TestForAuthenticated):
    """An access row below the manager level is not enough."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event, user) -> None:
        t_event.acl.create(user=user, level=Permission.GUEST)
        api_client.force_authenticate(user=user)


class TestForEventManager(TestForAuthenticated):
    """An administrator access row on the event."""

    can_manage = True
    level = Permission.ADMIN
    expected_status_codes: dict[str, status] = {
        "list": status.OK,
        "create": status.CREATED,
        "retrieve": status.OK,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_event, user) -> None:
        t_event.acl.create(user=user, level=self.level)
        api_client.force_authenticate(user=user)


class TestForEventOwner(TestForEventManager):
    """An owner access row is above the manager level."""

    level = Permission.OWNER


class TestForStaff(TestForEventManager):
    """Platform staff manage every event, with or without an access row, as they do for the related files."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, db) -> None:
        api_client.force_authenticate(user=UserFactory(is_staff=True))
