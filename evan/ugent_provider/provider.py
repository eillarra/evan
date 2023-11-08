from allauth.socialaccount.providers.microsoft.provider import MicrosoftGraphAccount, MicrosoftGraphProvider

from .views import UGentMicrosoftOAuth2Adapter


class UGentAccount(MicrosoftGraphAccount):
    """UGent account."""


class UGentMicrosoftProvider(MicrosoftGraphProvider):
    """UGent Microsoft provider."""

    id = "ugent"
    name = "UGent"
    account_class = UGentAccount
    oauth2_adapter_class = UGentMicrosoftOAuth2Adapter


provider_classes = [UGentMicrosoftProvider]
