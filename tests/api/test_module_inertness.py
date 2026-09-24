"""Tests for module inertness: disabled modules are invisible and inert on the API.

For a disabled module, its event-scoped routes yield empty lists and refuse
mutations for that event; toggling the module back on restores them. The data
guard prevents disabling a module that holds data, so these tests create the
data only while the module is enabled and clean it up before toggling off.
"""

from http import HTTPStatus as status

import pytest
from django.urls import reverse

from tests._factories import EventFactory, KeynoteFactory, PaperFactory, SessionFactory, UserFactory


@pytest.fixture
def manager(db):
    return UserFactory()


def _event_with_manager(module_keys: tuple[str, ...] = ()):
    """Create a listed event with the given modules enabled and a manager on the ACL.

    :param module_keys: The module keys to enable on the event.
    :returns: A tuple of (event, manager_user).
    """
    from evan.models.rel.permissions import Permission

    modules = {key: key in module_keys for key in ("payments", "content", "program", "papers", "communications")}
    event = EventFactory(config={"modules": modules})
    manager = UserFactory()
    event.acl.create(user=manager, level=Permission.ADMIN)
    return event, manager


def _list_url(name: str, event) -> str:
    return reverse(f"v1:{name}-list", args=[event.code])


MODULE_ROUTES = {
    "papers": ("papers", PaperFactory),
    "program": ("sessions", SessionFactory),
    "content": ("keynotes", KeynoteFactory),
}


@pytest.mark.api
@pytest.mark.django_db
class TestModuleScopedRoutesInert:
    """Disabled modules yield empty lists and refuse creates on their routes."""

    @pytest.mark.parametrize("module_key,route_name,factory", [(k, r, f) for k, (r, f) in MODULE_ROUTES.items()])
    def test_disabled_module_yields_empty_list(self, module_key, route_name, factory, api_client):
        event, manager = _event_with_manager()  # all modules disabled
        api_client.force_authenticate(user=manager)

        response = api_client.get(_list_url(route_name, event))

        assert response.status_code == status.OK
        assert response.data == []

    def test_enabled_module_lists_data(self, api_client):
        event, manager = _event_with_manager(("papers",))
        PaperFactory(event=event, session=None)
        api_client.force_authenticate(user=manager)

        response = api_client.get(_list_url("papers", event))

        assert response.status_code == status.OK
        assert len(response.data) == 1

    def test_disabled_module_refuses_create(self, api_client):
        event, manager = _event_with_manager()  # papers disabled
        api_client.force_authenticate(user=manager)

        response = api_client.post(
            _list_url("papers", event), {"title": "P", "abstract": "A", "doi": ""}, format="json"
        )

        assert response.status_code == status.FORBIDDEN

    def test_enabled_module_accepts_create(self, api_client):
        event, manager = _event_with_manager(("papers",))
        api_client.force_authenticate(user=manager)

        response = api_client.post(
            _list_url("papers", event), {"title": "P", "abstract": "A", "doi": ""}, format="json"
        )

        assert response.status_code == status.CREATED

    def test_toggling_module_off_hides_data_and_on_restores_it(self, api_client):
        event, manager = _event_with_manager(("program",))
        SessionFactory(event=event)
        api_client.force_authenticate(user=manager)

        assert len(api_client.get(_list_url("sessions", event)).data) == 1

        event.sessions.all().delete()
        event.config = {}
        event.save()
        event.refresh_from_db()
        assert api_client.get(_list_url("sessions", event)).data == []

        event.config = {"modules": {"program": True}}
        event.save()
        event.refresh_from_db()
        assert api_client.get(_list_url("sessions", event)).data == []

        SessionFactory(event=event)
        assert len(api_client.get(_list_url("sessions", event)).data) == 1


@pytest.mark.api
@pytest.mark.django_db
class TestCommunicationsModuleInertness:
    """Email plans are hidden and inert when the communications module is off."""

    def test_disabled_communications_hides_emailplans(self, api_client):
        event, manager = _event_with_manager()
        api_client.force_authenticate(user=manager)

        response = api_client.get(_list_url("emailplans", event))

        assert response.status_code == status.OK
        assert response.data == []

    def test_enabled_communications_lists_emailplans(self, api_client):
        from evan.models import EmailPlan

        event, manager = _event_with_manager(("communications",))
        EmailPlan.objects.create(event=event, name="Plan", subject="S", body="B")
        api_client.force_authenticate(user=manager)

        response = api_client.get(_list_url("emailplans", event))

        assert response.status_code == status.OK
        assert len(response.data) == 1


@pytest.mark.api
@pytest.mark.django_db
class TestPaymentsModuleInertness:
    """Coupons are hidden when the payments module is off."""

    def test_disabled_payments_hides_coupons(self, api_client):
        event, manager = _event_with_manager()
        api_client.force_authenticate(user=manager)

        response = api_client.get(_list_url("coupons", event))

        assert response.status_code == status.OK
        assert response.data == []

    def test_enabled_payments_lists_coupons(self, api_client):
        from tests._factories import CouponFactory

        event, manager = _event_with_manager(("payments",))
        CouponFactory(event=event)
        api_client.force_authenticate(user=manager)

        response = api_client.get(_list_url("coupons", event))

        assert response.status_code == status.OK
        assert len(response.data) == 1
