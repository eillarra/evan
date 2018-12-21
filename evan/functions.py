from celery.execute import send_task as celery_send_task
from django.conf import settings


def send_task(*args, **kwargs):
    if not settings.DEBUG:
        celery_send_task(*args, **kwargs)
