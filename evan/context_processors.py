import os


def app(request):
    return {
        'CONTACT_EMAIL': 'evan@ugent.be'
    }


def sentry(request):
    return {
        'GIT_REV': os.environ.get('GIT_REV', None)
    }
