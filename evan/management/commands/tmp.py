from django.core.management.base import BaseCommand

from evan.services.s3 import empty_bucket


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        empty_bucket("evan-staging")
