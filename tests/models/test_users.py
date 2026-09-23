from unittest.mock import Mock

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.db import connection
from django.test.utils import CaptureQueriesContext

from evan.models import User
from evan.models.users import _strip_emoji, _username_with_suffix, link_to_existing_user
from evan.ugent_provider.provider import UGENT_PROVIDER_ID
from tests._factories import AffiliationDomainFactory, UserFactory


def test_affiliation_updates(db):
    """Test that the affiliation and country are set correctly based on the email domain."""

    AffiliationDomainFactory(fld="example.com", affiliation="Example Inc.", country="BE")
    user = UserFactory(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        affiliation="",
        country="",
    )

    assert user.affiliation == "Example Inc."
    assert user.country == "BE"


@pytest.mark.parametrize(
    ("base", "suffix", "expected"),
    [
        ("bob", 1, "bob1"),
        ("alice", 3, "alice3"),
        ("a" * 145, 99, "a" * 145 + "99"),  # under max (147 chars)
        ("a" * 149, 1, "a" * 149 + "1"),  # exactly max (150 chars)
        ("a" * 150, 1, "a" * 149 + "1"),  # truncate base by 1
        ("a" * 150, 123, "a" * 147 + "123"),  # truncate base by 3
    ],
)
def test_username_with_suffix(base, suffix, expected):
    """Suffix appended correctly and total length never exceeds 150."""
    result = _username_with_suffix(base, suffix)
    assert result == expected
    assert len(result) <= 150


def test_save_retries_username_collision(db):
    """Saving a user whose username collides gets a numeric suffix instead of raising."""
    from evan.models import User

    UserFactory(username="asthaanand")

    user = User(username="asthaanand", email="other@example.com")
    user.save()

    assert user.username == "asthaanand1"
    assert User.objects.filter(username="asthaanand1").exists()


def test_save_retries_multiple_collisions(db):
    """Retry increments until a free slot is found."""
    from evan.models import User

    UserFactory(username="dup")
    UserFactory(username="dup1")
    UserFactory(username="dup2")

    user = User(username="dup", email="another@example.com")
    user.save()

    assert user.username == "dup3"


def test_save_update_preserves_username(db):
    """Updating an existing user keeps the username unchanged (no retry path)."""
    user = UserFactory(username="original")
    user.first_name = "Changed"
    user.save()

    user.refresh_from_db()
    assert user.username == "original"
    assert user.first_name == "Changed"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Claassen 🟥", "Claassen"),  # EVAN-BACKEND-4V: LinkedIn emoji in last_name
        ("Jane 🎉 Doe", "Jane Doe"),
        ("Hello 😀 World 🌍", "Hello World"),
        ("Plain ASCII", "Plain ASCII"),
        ("Café Müller", "Café Müller"),  # accented Latin stays (BMP)
        ("北京", "北京"),  # CJK stays (BMP)
        ("", ""),
        (None, ""),
        ("🟥", ""),  # only emoji
        ("Trailing space ", "Trailing space"),  # strip() removes whitespace
    ],
)
def test_strip_emoji(value, expected):
    """Supplementary-plane code points are removed; BMP characters are preserved."""
    assert _strip_emoji(value) == expected


def test_save_strips_emoji_from_name_fields(db):
    """Saving a user with emoji in first/last name stores the sanitized values.

    Regression test for EVAN-BACKEND-4V: LinkedIn callback received ``last_name``
    containing U+1F7E5 (🟥) and the non-utf8mb4 column raised OperationalError 1366.
    """
    user = UserFactory(first_name="Jane 🎉", last_name="Claassen 🟥")

    user.refresh_from_db()
    assert user.first_name == "Jane"
    assert user.last_name == "Claassen"


def test_save_strips_emoji_on_update(db):
    """Updating an existing user's name also strips emoji."""
    user = UserFactory(first_name="Plain", last_name="Name")
    user.last_name = "Updated 🟥"
    user.save()

    user.refresh_from_db()
    assert user.last_name == "Updated"


# ---------------------------------------------------------------------------
# Affiliation auto-fill (pinned: display-only, never an access input)
# ---------------------------------------------------------------------------


def test_affiliation_stays_empty_for_unknown_domain(db):
    """An unknown e-mail domain leaves affiliation and country empty, without error."""
    user = UserFactory(email="someone@gmail.com", affiliation="", country="")

    assert user.affiliation == ""
    assert user.country == ""


def test_affiliation_not_overwritten_on_login(db):
    """An already-set affiliation is never overwritten by the auto-fill."""
    AffiliationDomainFactory(fld="example.com", affiliation="Example Inc.", country="BE")

    user = UserFactory(
        email="jane@example.com",
        affiliation="Ghent University",
        country="",
    )

    assert user.affiliation == "Ghent University"
    assert user.country == "BE"  # country is still filled when empty


# ---------------------------------------------------------------------------
# UGent verification (identity/ugent-verification)
# ---------------------------------------------------------------------------


def test_is_ugent_verified_with_linked_ugent_account(db):
    """A user with a linked UGent-provider social account is UGent-verified."""
    user = UserFactory()
    SocialAccount.objects.create(user=user, provider=UGENT_PROVIDER_ID, uid="ug-1")

    assert user.is_ugent_verified is True


def test_is_ugent_verified_false_with_other_provider(db):
    """A linked account from another provider does not make the user UGent-verified."""
    user = UserFactory()
    SocialAccount.objects.create(user=user, provider="github", uid="gh-1")

    assert user.is_ugent_verified is False


def test_is_ugent_verified_false_without_accounts(db):
    """A user with no linked social accounts is not UGent-verified."""
    assert UserFactory().is_ugent_verified is False


def test_unlinking_ugent_account_removes_verification(db):
    """Removing the only linked UGent-provider account flips verification to False."""
    user = UserFactory()
    account = SocialAccount.objects.create(user=user, provider=UGENT_PROVIDER_ID, uid="ug-1")
    assert user.is_ugent_verified is True

    account.delete()

    assert user.is_ugent_verified is False


def test_ugent_verified_queryset_filters_in_single_query(db):
    """The queryset returns exactly the UGent-verified users in a single query."""
    verified = UserFactory()
    UserFactory()
    SocialAccount.objects.create(user=verified, provider=UGENT_PROVIDER_ID, uid="ug-2")

    with CaptureQueriesContext(connection) as queries:
        result = list(User.objects.ugent_verified())

    assert len(queries.captured_queries) == 1
    assert result == [verified]


# ---------------------------------------------------------------------------
# UGent login linking (pinned behavior of link_to_existing_user)
# ---------------------------------------------------------------------------


def _fake_sociallogin(provider: str, extra_data: dict, is_existing: bool = False) -> Mock:
    """Build a minimal sociallogin stand-in with a Mock connect method.

    :param provider: The provider id of the social account.
    :param extra_data: The extra data carried by the social account.
    :param is_existing: Whether the sociallogin is already linked to a user.
    :returns: A Mock shaped like an allauth SocialLogin.
    """
    sociallogin = Mock(is_existing=is_existing)
    sociallogin.account.provider = provider
    sociallogin.account.extra_data = extra_data
    return sociallogin


def test_ugent_login_links_existing_user_by_verified_email(db):
    """A UGent login whose mail matches a verified e-mail links to that user."""
    user = UserFactory(email="jane@ugent.be", affiliation="", country="")
    EmailAddress.objects.create(user=user, email="jane@ugent.be", verified=True, primary=True)

    sociallogin = _fake_sociallogin(UGENT_PROVIDER_ID, {"mail": "jane@ugent.be"})
    link_to_existing_user(None, request=None, sociallogin=sociallogin)

    sociallogin.connect.assert_called_once_with(None, user)


def test_ugent_login_does_not_link_unverified_email(db):
    """An unverified e-mail never links a UGent login to an existing user."""
    user = UserFactory(email="jane@ugent.be", affiliation="", country="")
    EmailAddress.objects.create(user=user, email="jane@ugent.be", verified=False, primary=True)

    sociallogin = _fake_sociallogin(UGENT_PROVIDER_ID, {"mail": "jane@ugent.be"})
    link_to_existing_user(None, request=None, sociallogin=sociallogin)

    sociallogin.connect.assert_not_called()


def test_ugent_login_without_mail_does_not_link(db):
    """A UGent login whose extra data lacks a mail address is not linked."""
    sociallogin = _fake_sociallogin(UGENT_PROVIDER_ID, {})
    link_to_existing_user(None, request=None, sociallogin=sociallogin)

    sociallogin.connect.assert_not_called()


def test_non_ugent_login_does_not_link_by_email(db):
    """Only UGent-provider logins use e-mail-based linking."""
    user = UserFactory(email="jane@ugent.be", affiliation="", country="")
    EmailAddress.objects.create(user=user, email="jane@ugent.be", verified=True, primary=True)

    sociallogin = _fake_sociallogin("github", {"mail": "jane@ugent.be"})
    link_to_existing_user(None, request=None, sociallogin=sociallogin)

    sociallogin.connect.assert_not_called()


def test_existing_sociallogin_is_left_alone(db):
    """An already-linked social login skips the linking receiver entirely."""
    sociallogin = _fake_sociallogin(UGENT_PROVIDER_ID, {"mail": "jane@ugent.be"}, is_existing=True)
    link_to_existing_user(None, request=None, sociallogin=sociallogin)

    sociallogin.connect.assert_not_called()
