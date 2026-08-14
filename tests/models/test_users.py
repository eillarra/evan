import pytest

from evan.models.users import _strip_emoji, _username_with_suffix
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
