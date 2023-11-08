from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import UGentMicrosoftProvider


urlpatterns = default_urlpatterns(UGentMicrosoftProvider)
