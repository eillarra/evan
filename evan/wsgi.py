# https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise


env = os.environ.get("DJANGO_ENV", None)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evan.settings")
os.environ["HTTPS"] = "on"

application = get_wsgi_application()
application = WhiteNoise(application, root=os.path.join(settings.SITE_ROOT, "www"), max_age=31536000)
