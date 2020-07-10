import os

from evan.models import Event


def app(request):
    return {
        "UPCOMING_EVENTS": Event.objects.upcoming(),
        "CONTACT_EMAIL": "evan@ugent.be",
    }


def sentry(request):
    return {"GIT_REV": os.environ.get("GIT_REV", None)}
