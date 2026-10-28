"""Tests for the secret-editor URLs: an unknown paper or session UUID is a 404."""

import uuid
from http import HTTPStatus

import pytest
from django.urls import reverse

from tests._factories import PaperFactory, SessionFactory


@pytest.mark.site
@pytest.mark.django_db
class TestPaperSecretEditor:
    """The paper editor is reachable only through a known UUID and the right secret."""

    def test_unknown_uuid_is_not_found(self, client):
        """A well-formed UUID that matches no paper is a 404, not a server error."""
        url = reverse("paper:secret", args=[uuid.uuid4(), "x"])

        assert client.get(url).status_code == HTTPStatus.NOT_FOUND

    def test_known_uuid_with_the_wrong_secret_is_refused(self, client):
        """The view is reached for a known paper, so the 404 above is about the UUID."""
        paper = PaperFactory()

        assert client.get(f"/p/{paper.uuid}/wrong-secret/").status_code == HTTPStatus.FORBIDDEN

    def test_known_uuid_with_the_right_secret_renders(self, client):
        paper = PaperFactory()

        assert client.get(paper.get_secret_url()).status_code == HTTPStatus.OK


@pytest.mark.site
@pytest.mark.django_db
class TestSessionSecretEditor:
    """The session editor is reachable only through a known UUID and the right secret."""

    def test_unknown_uuid_is_not_found(self, client):
        """A well-formed UUID that matches no session is a 404, not a server error."""
        url = reverse("session:secret", args=[uuid.uuid4(), "x"])

        assert client.get(url).status_code == HTTPStatus.NOT_FOUND

    def test_known_uuid_with_the_wrong_secret_is_refused(self, client):
        """The view is reached for a known session, so the 404 above is about the UUID."""
        session = SessionFactory()

        assert client.get(f"/s/{session.uuid}/wrong-secret/").status_code == HTTPStatus.FORBIDDEN

    def test_known_uuid_with_the_right_secret_renders(self, client):
        session = SessionFactory()

        assert client.get(session.get_secret_url()).status_code == HTTPStatus.OK
