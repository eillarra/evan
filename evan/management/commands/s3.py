from django.core.management.base import BaseCommand

from evan.services.s3 import list_bucket_files


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """List all files in the S3 bucket."""
        self.stdout.write("Listing all files in the S3 bucket...")
        files = list_bucket_files("evan")
        for file in files:
            self.stdout.write(file)
        self.stdout.write("Done.")
