"""Behavior tests for the remarks API, as used by the managers of an event."""

from http import HTTPStatus as status

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.urls import reverse

from evan.models.rel.remarks import Remark
from tests._factories import RegistrationFactory, UserFactory


NOTE = "Original note"

pytestmark = [pytest.mark.api, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def authenticate(api_client, t_event_manager) -> None:
    api_client.force_authenticate(user=t_event_manager)


@pytest.fixture
def registration(t_event):
    return RegistrationFactory(event=t_event, user=UserFactory())


def remark_kwargs(obj: Model) -> dict[str, int]:
    return {
        "parent_lookup_content_type_id": ContentType.objects.get_for_model(obj).id,
        "parent_lookup_object_id": obj.pk,
    }


def test_create_records_the_author(api_client, registration, t_event_manager) -> None:
    response = api_client.post(
        reverse("v1:remark-list", kwargs=remark_kwargs(registration)), {"text": "New note"}, format="json"
    )

    assert response.status_code == status.CREATED
    assert Remark.objects.get(text="New note").created_by == t_event_manager


@pytest.mark.parametrize("country", ["", "NL"])
def test_author_country_is_rendered_as_a_plain_code(api_client, registration, country) -> None:
    author = UserFactory(country=country)
    Remark.objects.create(content_object=registration, text=NOTE, created_by=author)

    response = api_client.get(reverse("v1:remark-list", kwargs=remark_kwargs(registration)))

    assert response.status_code == status.OK
    assert response.json()[0]["created_by"]["country"] == country


def test_remark_of_another_registration_is_not_reachable(api_client, t_event, registration) -> None:
    other = RegistrationFactory(event=t_event, user=UserFactory())
    foreign = Remark.objects.create(content_object=other, text="Foreign note")

    response = api_client.get(reverse("v1:remark-detail", kwargs={**remark_kwargs(registration), "pk": foreign.pk}))

    assert response.status_code == status.NOT_FOUND
