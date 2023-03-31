from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import UgentMicrosoftProvider


urlpatterns = default_urlpatterns(UgentMicrosoftProvider)
