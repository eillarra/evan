import logging

from .base import *  # noqa


DEBUG = True
TEST = True

ALLOWED_HOSTS = ("localhost",)
INTERNAL_IPS = ("127.0.0.1",)


# https://gauravvjn.medium.com/11-tips-for-lightning-fast-tests-in-django-effa87383040

logging.disable()

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


# https://docs.djangoproject.com/en/dev/ref/settings/#databases


class DisableMigrations(dict):
    """Disable migrations during testing for speed."""

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}
MIGRATION_MODULES = DisableMigrations()


# https://docs.djangoproject.com/en/dev/topics/cache/

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}


# https://docs.djangoproject.com/en/dev/topics/email/

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# https://django-compressor.readthedocs.io/en/stable/settings/

COMPRESS_ENABLED = False


# https://github.com/MrBin99/django-vite

DJANGO_VITE["default"]["dev_mode"] = True  # noqa
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
