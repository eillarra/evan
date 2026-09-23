# flake8: noqa

import os

# Dispatch to the environment-specific settings module only when the package itself
# is the settings module (manage.py / wsgi.py default to "evan.settings"). When a
# specific module is requested (e.g. DJANGO_SETTINGS_MODULE=evan.settings.test), stay
# inert so that importing the package does not eagerly load a different environment.

settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

if settings_module in ("", "evan.settings"):
    env = os.environ.get("DJANGO_ENV", "development")

    if env in {"production", "staging"}:
        from .production import *
    elif env == "test":
        from .test import *
    else:
        from .development import *
