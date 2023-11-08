import os


def app(request):
    return {
        "DJANGO_ENV": os.environ.get("DJANGO_ENV", "development"),
    }


def sentry(request):
    return {
        "GIT_REV": os.environ.get("GIT_REV", None),
    }
