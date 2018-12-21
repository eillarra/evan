import os

from .base import *  # noqa


DEBUG = False

ALLOWED_HOSTS = (os.environ.get('DJANGO_ALLOWED_HOST', 'evan.ugent.be'),)
MEDIA_ROOT = '/storage/media/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = True

CRISPY_FAIL_SILENTLY = True


# sendfile

SENDFILE_ROOT = f'{MEDIA_ROOT}private'
SENDFILE_URL = '/-internal'


# https://docs.djangoproject.com/en/2.2/topics/cache/

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    },
    'staticfiles': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'django-staticfiles',
    },
}

CACHE_MIDDLEWARE_SECONDS = 30
USE_ETAGS = True


# http://celery.readthedocs.org/en/latest/django/

CELERY_BROKER_URL = os.environ.get('RABBITMQ_URL')


# https://docs.djangoproject.com/en/2.2/topics/email/

DEFAULT_FROM_EMAIL = 'Evan <evan@ugent.be>'
SERVER_EMAIL = 'evan@ugent.be'
EMAIL_SUBJECT_PREFIX = '[Evan] '

EMAIL_HOST = 'smtprelay.ugent.be'
EMAIL_PORT = 25


# http://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa
    'rest_framework.renderers.JSONRenderer',
)


# https://docs.djangoproject.com/en/2.2/topics/logging/#django-security
# https://docs.sentry.io/platforms/python/?platform=python

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
