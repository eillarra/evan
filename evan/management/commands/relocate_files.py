"""Relocate stored files to the visibility-free storage layout.

Files uploaded before the visibility tiers existed are stored under a key that
starts with their old visibility (``public/…`` or ``private/…``). The key no
longer means anything — the guard decides access — so this command copies those
objects to the visibility-free layout and rewrites the rows.

The old objects are kept unless ``--delete-source`` is passed, and the command
is safe to run twice: the old layout keeps working, so a failed run changes
nothing. Deletion goes through the shared S3 helper, so it only happens in
production.

Rewriting a row changes the address the file is served at: media delivery looks
the file up by its stored name. The temporary fallback in ``MediaFileView``
resolves the old ``/media/public/…`` and ``/media/private/…`` addresses to the
moved object, so links already handed out (emails, pasted URLs) keep working;
removing that fallback together with this command is what finally breaks them.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from evan.models import File
from evan.services.s3 import copy_s3_object, delete_s3_object, get_s3_client


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
            help=(
                "Delete the old object after copying it, in production only. "
                "Off by default: the old layout keeps working."
            ),
        )

    def handle(self, *args, **options) -> None:
        """Relocate the legacy files.

        :param args: Positional arguments (unused).
        :param options: The parsed options.
        :raises CommandError: If the storage backend cannot be reached.
        """
        dry_run = options.get("dry_run", False)
        delete_source = options.get("delete_source", False)
        legacy_query = Q()

        for prefix in LEGACY_PREFIXES:
            legacy_query |= Q(file__startswith=prefix)

        legacy_files = File.objects.filter(legacy_query).order_by("pk")

        # Snapshot the ids: the loop rewrites the very column the filter reads,
        # so iterating a live queryset could skip rows.
        legacy_pks = list(legacy_files.values_list("pk", flat=True))
        if not legacy_pks:
            self.stdout.write("No files to relocate.")
            return

        self.stdout.write(f"Found {len(legacy_pks)} file(s) to relocate.")

        if delete_source and settings.ENV != "production":
            self.stdout.write(
                self.style.WARNING("Source deletion is skipped outside production; the old objects stay in place.")
            )

        if not dry_run:
            try:
                get_s3_client()
            except Exception as exc:
                raise CommandError(f"Could not reach the storage backend: {exc}") from exc

        relocated = 0

        for file_pk in legacy_pks:
            file = File.objects.filter(pk=file_pk).first()
            if file is None:
                continue

            source_key = file.s3_object_key
            destination_key = self.destination_key(file)

            if source_key == destination_key:
                continue

            self.stdout.write(f"  {file.pk}: {source_key} -> {destination_key}")

            if dry_run:
                relocated += 1
                continue

            copy_s3_object(source_key, destination_key)

            # The row must point at the copy before the source goes: a failed
            # save then leaves a re-runnable file rather than a dangling row.
            file.file.name = destination_key
            file.save(update_fields=["file"])

            if delete_source:
                delete_s3_object(source_key)

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
