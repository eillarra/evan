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
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

CACHE_MIDDLEWARE_SECONDS = 20


# https://docs.djangoproject.com/en/dev/topics/email/

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# https://github.com/MrBin99/django-vite

DJANGO_VITE["default"]["dev_mode"] = True  # noqa
