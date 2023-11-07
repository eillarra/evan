from allauth.socialaccount.providers.microsoft.provider import MicrosoftGraphProvider


class UgentMicrosoftProvider(MicrosoftGraphProvider):
    id = "ugent"
    name = "UGent"


provider_classes = [UgentMicrosoftProvider]
