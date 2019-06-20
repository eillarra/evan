import os

from django.contrib.messages import constants as messages
from kombu import Queue
from urllib.parse import urlparse


PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECT_ROOT = os.path.abspath(os.path.join(PACKAGE_ROOT, os.pardir))
SITE_ROOT = os.path.join(PACKAGE_ROOT, 'site')


# General configuration

DEBUG = True

ADMINS = (('eillarra', 'eillarra@ugent.be'),)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'DJANGO_SECRET_KEY')
SITE_ID = int(os.environ.get('SITE_ID', 1))

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'django.contrib.redirects',
    'django.contrib.sessions',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    # helpers
    'captcha',
    'compressor',
    'crispy_forms',

    # auth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.linkedin_oauth2',
    # 'allauth.socialaccount.providers.twitter',

    # evan
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'evan',
    'evan.api',
    'evan.site',

    # admin
    'django.contrib.admin',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dnt.middleware.DoNotTrackMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]


ROOT_URLCONF = 'evan.urls'
WSGI_APPLICATION = 'evan.wsgi.app'


# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

db = urlparse(os.environ.get('DATABASE_URL'))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': db.path[1:],
        'USER': db.username,
        'PASSWORD': db.password,
        'HOST': db.hostname,
        'PORT': db.port,
    }
}


# Time zones
# https://docs.djangoproject.com/en/2.2/topics/i18n/timezones/

USE_TZ = True
TIME_ZONE = 'Europe/Brussels'


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en'
USE_I18N = False
USE_L10N = False

FIRST_DAY_OF_WEEK = 1


# Security
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

# CSRF / Cookie

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_USE_SESSIONS = not DEBUG

# XFRAME

X_FRAME_OPTIONS = 'DENY'
CORS_ORIGIN_ALLOW_ALL = True

# Account

LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'dashboard'

ACCOUNT_ACTIVATION_DAYS = 7
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_FORMS = {
    'signup': 'evan.forms.EvanSignupForm',
}

# Social accounts

SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': [
            'user'
        ],
    },
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'linkedin_oauth2': {
        'SCOPE': [
            'r_emailaddress',
            'r_liteprofile',
        ],
        'PROFILE_FIELDS': [
            'id',
            'firstName',
            'lastName',
            'emailAddress',
        ]
    },
}


# http://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_VERSION': 'v1',
    'PAGE_SIZE': 100,
}


# https://docs.djangoproject.com/en/2.2/topics/templates/

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(SITE_ROOT, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'evan.context_processors.app',
                'evan.context_processors.sentry',
            ],
        },
    },
]

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

COUNTRIES_OVERRIDE = {
    'GB': 'United Kingdom',
    'US': 'United States',
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
# https://docs.djangoproject.com/en/2.2/howto/static-files/deployment/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(SITE_ROOT, 'www', 'static')
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'static'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'compressor.finders.CompressorFinder',
)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
COMPRESS_OFFLINE = True
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)


# File uploads
# https://docs.djangoproject.com/en/2.2/topics/http/file-uploads/

FILE_UPLOAD_PERMISSIONS = 0o644


# http://stackoverflow.com/questions/24071290/
# https://docs.djangoproject.com/en/2.2/ref/settings/#media-root

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(SITE_ROOT, 'www', 'media')


# http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#celerytut-configuration

task_default_queue = 'evan'
CELERY_TASK_QUEUES = [Queue(name=task_default_queue)]
CELERY_TASK_DEFAULT_QUEUE = task_default_queue

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False


# reCAPTCHA
# https://github.com/praekelt/django-recaptcha#installation

RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', 'RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', 'RECAPTCHA_PRIVATE_KEY')
RECAPTCHA_USE_SSL = True
NOCAPTCHA = True  # For using reCAPTCHA v2


# https://django-crispy-forms.readthedocs.io/en/latest/index.html

CRISPY_TEMPLATE_PACK = 'bootstrap4'
