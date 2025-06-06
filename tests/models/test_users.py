from evan.utils.factories import AffiliationDomainFactory, UserFactory


def test_affiliation_updates(db):
    """Test that the affiliation and country are set correctly based on the email domain."""

    AffiliationDomainFactory(fld="example.com", affiliation="Example Inc.", country="BE")
    user = UserFactory(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
    )

    assert user.affiliation == "Example Inc."
    assert user.country == "BE"
