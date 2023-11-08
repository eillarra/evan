# from allauth.account.views import logout
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.views.i18n import set_language

from evan.site.views.files import MediaFileView


admin.autodiscover()


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("evan.api.urls")),
    path("i18n/setlang/", set_language, name="set_language"),
    # allauth
    path("u/", include("allauth.urls")),
    # media
    path("media/<path:file>", MediaFileView.as_view(), name="media_file"),
    # site
    path("", include("evan.site.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()


# error handlers

handler500 = "evan.site.views.errors.server_error"
