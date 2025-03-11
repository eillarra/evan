import os
import re

import sentry_sdk
from django.core.exceptions import DisallowedHost
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = (os.environ.get("DJANGO_ALLOWED_HOST", "evan.ugent.be"),)
MEDIA_ROOT = "/storage/media/"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = True


# https://docs.djangoproject.com/en/dev/ref/settings/#storages
# https://django-storages.readthedocs.io/en/latest/

AWS_S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
AWS_QUERYSTRING_AUTH = False
AWS_IS_GZIPPED = True

STORAGES = {
    "default": {
        "BACKEND": "evan.services.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# https://docs.sentry.io/platforms/python/guides/django/
# https://github.com/getsentry/sentry-python/issues/149#issuecomment-1056642777


def before_send(event, hint):
    """
    Ignore some exceptions.
    """
    if "exc_info" in hint:
        errors_to_ignore = (DisallowedHost,)
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, errors_to_ignore):
            return None
    return event


sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DJANGO_DSN", None),
    release=os.environ.get("GIT_REV", None),
    environment=os.environ.get("DJANGO_ENV", "production"),
    integrations=[DjangoIntegration(), RedisIntegration()],
    before_send=before_send,
    traces_sample_rate=0.1,
    # pii
    send_default_pii=True,
)


# https://docs.djangoproject.com/en/dev/topics/cache/

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
    },
    "staticfiles": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "django-staticfiles",
    },
}

CACHE_MIDDLEWARE_SECONDS = 30
USE_ETAGS = True


# https://docs.djangoproject.com/en/dev/topics/email/

DEFAULT_FROM_EMAIL = "Evan <evan@ugent.be>"
SERVER_EMAIL = "evan@ugent.be"
EMAIL_SUBJECT_PREFIX = "[Evan] "

EMAIL_HOST = "smtprelay.ugent.be"
EMAIL_PORT = 25


# https://docs.djangoproject.com/en/dev/topics/logging/#django-security
# https://docs.sentry.io/platforms/python/?platform=python

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}


# https://huey.readthedocs.io/en/latest/django.html

HUEY = {
    "huey_class": "huey.RedisHuey",
    "immediate": False,
    "name": "evan",
    "connection": {
        "url": f"{os.environ.get('REDIS_URL', 'redis://localhost:6379')}/10",
    },
}


# https://github.com/MrBin99/django-vite

DJANGO_VITE["default"]["dev_mode"] = False  # noqa


def immutable_file_test(path, url):
    # Vite generates files with 8 hash digits
    # Match filename with 8 or 12 hex digits before the extension
    # e.g. app.db8f2edc0c8a.js
    return re.match(r"^.+\.[0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test
