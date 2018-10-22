# https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toucon.settings.production')
os.environ['HTTPS'] = 'on'

application = get_wsgi_application()
application = WhiteNoise(application, root=os.path.join(settings.SITE_ROOT, 'www'), max_age=31536000)
