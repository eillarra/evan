"""Relocate stored files to the visibility-free storage layout.

Files uploaded before the visibility tiers existed are stored under a key that
starts with their old visibility (``public/…`` or ``private/…``). The key no
longer means anything — the guard decides access — so this command copies those
objects to the visibility-free layout and rewrites the rows.

The command is safe to run twice and never deletes the old objects: the old
layout keeps working, so a failed run changes nothing.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from evan.models import File
from evan.services.s3 import copy_s3_object, get_s3_client


LEGACY_PREFIXES = ("public/", "private/")


class Command(BaseCommand):
    """Move stored files to the visibility-free storage layout."""

    help = "Relocate files stored under a visibility-prefixed key to the visibility-free layout"

    def add_arguments(self, parser) -> None:
        """Add the command's arguments.

        :param parser: The argument parser.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be relocated without touching the storage or the database.",
        )
        parser.add_argument(
            "--delete-source",
            action="store_true",
            help="Delete the old object after copying it. Off by default: the old layout keeps working.",
        )

    def handle(self, *args, **options) -> None:
        """Relocate the legacy files.

        :param args: Positional arguments (unused).
        :param options: The parsed options.
        :raises CommandError: If the storage backend cannot be reached.
        """
        dry_run = options.get("dry_run", False)
        delete_source = options.get("delete_source", False)

        legacy_files = [file for file in File.objects.order_by("pk") if file.s3_object_key.startswith(LEGACY_PREFIXES)]
        if not legacy_files:
            self.stdout.write("No files to relocate.")
            return

        self.stdout.write(f"Found {len(legacy_files)} file(s) to relocate.")

        if not dry_run:
            try:
                get_s3_client()
            except Exception as exc:
                raise CommandError(f"Could not reach the storage backend: {exc}") from exc

        relocated = 0
        for file in legacy_files:
            source_key = file.s3_object_key
            destination_key = self.destination_key(file)

            if source_key == destination_key:
                continue

            self.stdout.write(f"  {file.pk}: {source_key} -> {destination_key}")

            if dry_run:
                relocated += 1
                continue

            copy_s3_object(source_key, destination_key)
            if delete_source:
                get_s3_client().delete_object(
                    Bucket=self._bucket_name(),
                    Key=source_key,
                )

            with transaction.atomic():
                file.file.name = destination_key
                file.save(update_fields=["file"])

            relocated += 1

        prefix = "Would relocate" if dry_run else "Relocated"
        self.stdout.write(self.style.SUCCESS(f"{prefix} {relocated} file(s)."))

    @staticmethod
    def destination_key(file: File) -> str:
        """Return the visibility-free key for a file.

        :param file: The file to relocate.
        :returns: The key the file should be stored at.
        """
        _, _, remainder = file.s3_object_key.partition("/")
        return f"files/{remainder}"

    @staticmethod
    def _bucket_name() -> str:
        """Return the configured bucket name."""
        import os

        return os.environ.get("S3_BUCKET_NAME", "")
