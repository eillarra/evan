import os

from .base import *  # noqa


DEBUG = False
APP_DOMAIN = 'toucon.net'
ALLOWED_HOSTS = (os.environ.get('DJANGO_ALLOWED_HOST', f'www.{APP_DOMAIN}'),)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = True

CRISPY_FAIL_SILENTLY = True


# https://docs.djangoproject.com/en/1.11/topics/cache/

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


# https://docs.djangoproject.com/en/1.11/topics/email/

EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'

DEFAULT_FROM_EMAIL = 'Toucon <dev@{0}>'.format(APP_DOMAIN)
SERVER_EMAIL = 'root@{0}'.format(APP_DOMAIN)
EMAIL_SUBJECT_PREFIX = '[{0}] '.format(APP_DOMAIN)

ANYMAIL = {
    'MAILGUN_API_KEY': os.environ.get('MAILGUN_API_KEY', 'MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN': 'mg.{0}'.format(APP_DOMAIN),
}


# http://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa
    'rest_framework.renderers.JSONRenderer',
)


# http://django-wkhtmltopdf.readthedocs.org/en/latest/

WKHTMLTOPDF_CMD = '/usr/bin/wkhtmltopdf'
WKHTMLTOPDF_CMD_OPTIONS = {
    'encoding': 'utf8',
    'quiet': True,
    'disable-javascript': True,
    'disable-smart-shrinking': True,
    'page-height': 297,
    'page-width': 210,
    'margin-top': 20,
    'margin-right': 20,
    'margin-bottom': 20,
    'margin-left': 20,
}


# https://docs.djangoproject.com/en/2.1/topics/logging/#django-security
# https://docs.sentry.io/platforms/python/?platform=python

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
