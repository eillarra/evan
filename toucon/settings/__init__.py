# flake8: noqa

import os


if os.environ.get('DJANGO_ENV', 'development') == 'production':
    from .production import *
else:
    from .development import *
