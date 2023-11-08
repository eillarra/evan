# flake8: noqa

import os

env = os.environ.get("DJANGO_ENV", "development")

if env in {"production", "staging"}:
    from .production import *
elif env == "test":
    from .test import *
else:
    from .development import *
