"""Tests for payments-module inertness in the registration flow.

When the payments module is disabled, a registration completes with no fee
resolution and no payment step; payments-enabled events keep today's behavior.
"""

from datetime import UTC, date, datetime, timedelta
from http import HTTPStatus as status

import pytest
from django.urls import reverse

from evan.api.serializers.events import EventSerializer
from tests._factories import EventFactory, UserFactory


def _open_event(config: dict):
    """Create a listed event with an open registration window and the given config.

    :param config: The event's config dict.
    :returns: The event.
    """
    event = EventFactory(
        config=config,
        registration_start_date=date.today() - timedelta(days=1),
        registration_deadline=datetime.now(UTC) + timedelta(days=30),
    )
    # The factory fills date fields with datetimes; reload to compare dates correctly.
    event.refresh_from_db()
    return event


@pytest.fixture
def payments_off_event(db):
    """A listed, open event with all modules disabled (no fees exist)."""
    return _open_event({"modules": {}})


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.api
@pytest.mark.django_db
class TestRegistrationOnPaymentsOffEvent:
    """Registration on a payments-off event completes with no fee or payment step."""

    def test_api_create_completes_with_zero_fee(self, api_client, payments_off_event, user):
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("v1:register-list", args=[payments_off_event.code]), {"fee_type": ""}, format="json"
        )

        assert response.status_code == status.CREATED
        registration = payments_off_event.registrations.get(user=user)
        assert registration.base_fee == 0
        assert registration.remaining_fee == 0

    def test_site_view_props_carry_no_fees(self, client, payments_off_event, user):
        client.force_login(user=user)
        request = client.get(reverse("registration:app", args=[payments_off_event.code])).wsgi_request

        data = EventSerializer(payments_off_event, context={"request": request}).data

        assert data["fees"] == []
        assert data["modules"]["payments"] is False

    def test_payment_view_refused_on_payments_off_event(self, client, payments_off_event, user):
        from tests._factories import RegistrationFactory

        registration = RegistrationFactory(event=payments_off_event, user=user, fee_type="")
        registration.base_fee = 0
        registration.paid = 0
        registration.saldo = 0
        registration.save()
        client.force_login(user=user)

        response = client.get(reverse("registration:payment", args=[registration.uuid]))

        assert response.status_code == status.FORBIDDEN

    def test_payments_on_event_unchanged(self, api_client, user):
        from evan.models import Fee

        event = _open_event(
            {"modules": {"payments": True, "content": True, "program": True, "papers": True, "communications": True}}
        )
        Fee.objects.create(event=event, type="regular", value=100)
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("v1:register-list", args=[event.code]), {"fee_type": "regular"}, format="json"
        )

        assert response.status_code == status.CREATED
        registration = event.registrations.get(user=user)
        assert registration.base_fee == 100
        assert registration.remaining_fee == 100
