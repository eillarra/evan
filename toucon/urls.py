from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponse


admin.autodiscover()

urlpatterns = [
    url(r'^_ah/health$', lambda request: HttpResponse()),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('toucon.api.urls')),
    url(r'^', include('toucon.site.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
