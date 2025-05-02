import hashlib
import random
import string

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Generates a random SHA256 hash."""

    def handle(self, *args, **kwargs):
        random_string = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(64))
        print(hashlib.sha256(random_string.encode("utf-8")).hexdigest())
