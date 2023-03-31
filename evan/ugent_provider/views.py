from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.microsoft.views import MicrosoftGraphOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView, OAuth2LoginView

from .provider import UgentMicrosoftProvider


class UgentMicrosoftOAuth2Adapter(MicrosoftGraphOAuth2Adapter):
    provider_id = UgentMicrosoftProvider.id

    settings = app_settings.PROVIDERS.get(provider_id, {})
    tenant = settings.get("TENANT")

    provider_base_url = "https://login.microsoftonline.com/{0}".format(tenant)
    access_token_url = "{0}/oauth2/v2.0/token".format(provider_base_url)
    authorize_url = "{0}/oauth2/v2.0/authorize".format(provider_base_url)


oauth2_login = OAuth2LoginView.adapter_view(UgentMicrosoftOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(UgentMicrosoftOAuth2Adapter)
