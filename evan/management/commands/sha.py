import hashlib
import secrets

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Generates a random SHA256 hash."""

    def handle(self, *args, **kwargs):
        random_string = secrets.token_urlsafe(64)
        print(hashlib.sha256(random_string.encode("utf-8")).hexdigest())
