from evan.ugent_provider.provider import UGENT_PROVIDER_ID, UGentMicrosoftProvider


def test_provider_id_matches_constant():
    """The provider id is defined once and referenced through the constant."""
    assert UGentMicrosoftProvider.id == UGENT_PROVIDER_ID == "ugent"
