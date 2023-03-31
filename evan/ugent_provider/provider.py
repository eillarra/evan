from allauth.socialaccount.providers.microsoft.provider import MicrosoftGraphProvider


class UgentMicrosoftProvider(MicrosoftGraphProvider):
    id = str("ugent")
    name = "UGent"


provider_classes = [UgentMicrosoftProvider]
