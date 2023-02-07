from .base import *  # noqa


DEBUG = True

ALLOWED_HOSTS = ("localhost",)
INTERNAL_IPS = ("127.0.0.1",)


# https://django-debug-toolbar.readthedocs.io/en/stable/

try:
    import debug_toolbar  # noqa

    INSTALLED_APPS += ("debug_toolbar",)  # noqa
    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)  # noqa
except ModuleNotFoundError:
    pass


# https://docs.djangoproject.com/en/dev/topics/cache/

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CACHE_MIDDLEWARE_SECONDS = 20


# https://docs.djangoproject.com/en/dev/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# http://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa
    "rest_framework.renderers.JSONRenderer",
    "evan.api.renderers.NoFormBrowsableAPIRenderer",
)
