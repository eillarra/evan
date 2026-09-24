"""Tests for the registration audience rule and the listing gate.

Covers:
  1. ``RegistrationView`` (site) and ``RegistrationCreateViewSet`` (API)
     enforcing ``registration_audience`` (``public`` / ``ugent_only``).
  2. Audience changes applying to new registrations only.
  3. The ``is_listed`` requirement at the registration entry points, with
     managers exempt through the existing preview flow.
"""

from http import HTTPStatus as status

import pytest
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse

from evan.ugent_provider.provider import UGENT_PROVIDER_ID
from tests._factories import EventFactory, RegistrationFactory, UserFactory


def _registration_url(event) -> str:
    return reverse("registration:app", args=[event.code])


def _api_registration_url(event) -> str:
    return reverse("v1:register-list", args=[event.code])


def _ugent_verified_user():
    """Create a user with a linked UGent-provider social account.

    :returns: A UGent-verified user.
    """
    user = UserFactory()
    SocialAccount.objects.create(user=user, provider=UGENT_PROVIDER_ID, uid=f"uid-{user.pk}")
    return user


@pytest.fixture
def open_public_event(db):
    """A listed, open-for-registration event with the public audience."""
    from datetime import UTC, date, datetime, timedelta

    from evan.models import Fee

    event = EventFactory(
        registration_start_date=date.today() - timedelta(days=1),
        registration_deadline=datetime.now(UTC) + timedelta(days=30),
    )
    Fee.objects.create(event=event, type="regular", value=100)
    return event


@pytest.mark.site
@pytest.mark.django_db
class TestRegistrationAudienceSite:
    """The site registration view enforces the audience rule."""

    def test_non_verified_user_blocked_on_ugent_only_event(self, client, open_public_event):
        open_public_event.registration_audience = "ugent_only"
        open_public_event.save()
        user = UserFactory()
        client.force_login(user=user)

        response = client.get(_registration_url(open_public_event))

        assert response.status_code == status.FORBIDDEN

    def test_verified_user_proceeds_on_ugent_only_event(self, client, open_public_event):
        open_public_event.registration_audience = "ugent_only"
        open_public_event.save()
        client.force_login(user=_ugent_verified_user())

        response = client.get(_registration_url(open_public_event))

        assert response.status_code == status.OK

    def test_any_user_proceeds_on_public_event(self, client, open_public_event):
        client.force_login(user=UserFactory())

        response = client.get(_registration_url(open_public_event))

        assert response.status_code == status.OK


@pytest.mark.api
@pytest.mark.django_db
class TestRegistrationAudienceApi:
    """The API registration create enforces the audience rule."""

    def test_non_verified_user_refused_with_ugent_detail(self, api_client, open_public_event):
        open_public_event.registration_audience = "ugent_only"
        open_public_event.save()
        api_client.force_authenticate(user=UserFactory())

        response = api_client.post(_api_registration_url(open_public_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.FORBIDDEN
        assert "UGent" in response.data["detail"]

    def test_verified_user_registers_on_ugent_only_event(self, api_client, open_public_event):
        open_public_event.registration_audience = "ugent_only"
        open_public_event.save()
        api_client.force_authenticate(user=_ugent_verified_user())

        response = api_client.post(_api_registration_url(open_public_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.CREATED

    def test_public_event_accepts_any_authenticated_user(self, api_client, open_public_event):
        api_client.force_authenticate(user=UserFactory())

        response = api_client.post(_api_registration_url(open_public_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.CREATED


@pytest.mark.django_db
class TestAudienceChangesApplyToNewRegistrationsOnly:
    """Tightening the audience never invalidates existing registrations."""

    def test_existing_registration_survives_audience_tightening(self, open_public_event):
        user = UserFactory()
        registration = RegistrationFactory(event=open_public_event, user=user, fee_type="regular")

        open_public_event.registration_audience = "ugent_only"
        open_public_event.save()
        registration.refresh_from_db()

        assert registration.is_accepted is not False
        assert open_public_event.registrations.filter(user=user).exists()


@pytest.mark.site
@pytest.mark.django_db
class TestRegistrationListingGateSite:
    """Only listed events take registrations; managers keep the preview flow."""

    def test_non_listed_event_refused_even_with_open_dates(self, client, open_public_event):
        open_public_event.listing_status = "pending_review"
        open_public_event.save()
        client.force_login(user=UserFactory())

        response = client.get(_registration_url(open_public_event))

        assert response.status_code == status.FORBIDDEN

    def test_same_event_proceeds_once_listed(self, client, open_public_event):
        client.force_login(user=UserFactory())

        response = client.get(_registration_url(open_public_event))

        assert response.status_code == status.OK

    def test_manager_still_opens_registration_of_unlisted_event(self, client, open_public_event):
        from evan.models.rel.permissions import Permission

        open_public_event.listing_status = "pending_review"
        open_public_event.save()
        manager = UserFactory()
        open_public_event.acl.create(user=manager, level=Permission.ADMIN)
        client.force_login(user=manager)

        response = client.get(_registration_url(open_public_event))

        assert response.status_code == status.OK

    def test_manager_preview_works_for_unlisted_event(self, client, open_public_event):
        from evan.models.rel.permissions import Permission

        open_public_event.listing_status = "pending_review"
        open_public_event.save()
        manager = UserFactory()
        open_public_event.acl.create(user=manager, level=Permission.ADMIN)
        client.force_login(user=manager)

        response = client.get(reverse("event:registration_preview", args=[open_public_event.code]))

        assert response.status_code == status.OK


@pytest.mark.api
@pytest.mark.django_db
class TestRegistrationListingGateApi:
    """The API registration create requires the event to be listed."""

    def test_non_listed_event_refused(self, api_client, open_public_event):
        open_public_event.listing_status = "pending_review"
        open_public_event.save()
        api_client.force_authenticate(user=UserFactory())

        response = api_client.post(_api_registration_url(open_public_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.FORBIDDEN

    def test_manager_can_register_on_unlisted_event(self, api_client, open_public_event):
        from evan.models.rel.permissions import Permission

        open_public_event.listing_status = "pending_review"
        open_public_event.save()
        manager = UserFactory()
        open_public_event.acl.create(user=manager, level=Permission.ADMIN)
        api_client.force_authenticate(user=manager)

        response = api_client.post(_api_registration_url(open_public_event), {"fee_type": "regular"}, format="json")

        assert response.status_code == status.CREATED
