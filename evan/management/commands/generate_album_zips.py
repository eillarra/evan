"""Management command to generate zip archives for album collections."""

import io
import zipfile
from pathlib import Path
from typing import Any

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError, CommandParser

from evan.models import Album, Event, File
from evan.services.s3 import get_s3_response


class Command(BaseCommand):
    """Management command to generate zip archives for album collections."""

    help = "Generate zip archives for album collections"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("event_code", type=str, help="Event code")
        parser.add_argument(
            "--album-id",
            type=int,
            help="Specific album ID to process (if not provided, all albums for the event will be processed)",
        )
        parser.add_argument(
            "--regenerate",
            action="store_true",
            help="Regenerate zip files even if they already exist",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be processed without actually creating zip files",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command execution.

        :param args: Additional arguments.
        :param options: Command options from add_arguments.
        """
        event_code = options["event_code"]
        album_id = options.get("album_id")
        regenerate = options["regenerate"]
        dry_run = options["dry_run"]

        # Get the event
        try:
            event = Event.objects.get(code=event_code)
        except Event.DoesNotExist as exc:
            raise CommandError(f"Event with code '{event_code}' does not exist.") from exc

        # Get albums to process
        if album_id:
            try:
                albums = [event.albums.get(id=album_id)]
            except Album.DoesNotExist as exc:
                raise CommandError(f"Album with ID {album_id} does not exist for event '{event_code}'.") from exc
        else:
            albums = list(event.albums.all())

        if not albums:
            self.stdout.write(self.style.WARNING("No albums found for the specified criteria."))
            return

        self.stdout.write(f"Found {len(albums)} album(s) to process:")
        for album in albums:
            self.stdout.write(f"  - {album.title} (ID: {album.id})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run mode - no files will be created."))
            return

        # Process each album
        for album in albums:
            self._process_album(album, regenerate)

        self.stdout.write(self.style.SUCCESS("Album zip generation completed."))

    def _process_album(self, album: Album, regenerate: bool) -> None:
        """Process a single album to generate its zip file.

        :param album: The album to process.
        :param regenerate: Whether to regenerate existing zip files.
        """
        self.stdout.write(f"\nProcessing album: {album.title}")

        # Check if zip file already exists
        existing_zip = album.get_collection_zip()
        if existing_zip and not regenerate:
            self.stdout.write(f"  Zip file already exists: {existing_zip.file.name}")
            return

        # Get original photos
        original_photos = album.get_original_photos()
        if not original_photos.exists():
            self.stdout.write(self.style.WARNING(f"  No original photos found in album '{album.title}'"))
            return

        self.stdout.write(f"  Found {original_photos.count()} original photo(s)")

        try:
            # Create zip file in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i, photo in enumerate(original_photos, 1):
                    self.stdout.write(f"    Adding photo {i}/{original_photos.count()}: {photo.file.name}")

                    try:
                        # Download the file from S3
                        response = get_s3_response(photo.s3_object_key)

                        # Get original filename or create a meaningful one
                        original_filename = Path(photo.file.name).name
                        if not original_filename or original_filename.startswith("files/"):
                            # Create a meaningful filename if the original is not descriptive
                            file_extension = Path(photo.file.name).suffix or ".jpg"
                            original_filename = f"photo_{i:03d}{file_extension}"

                        # Add file to zip
                        zip_file.writestr(original_filename, response.content)

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"    Failed to add photo {photo.file.name}: {str(e)}"))
                        continue

            # Create uploaded file from the zip buffer
            zip_buffer.seek(0)
            zip_filename = f"{album.event.code}_{album.title}_photos.zip".replace(" ", "_")

            zip_uploaded_file = SimpleUploadedFile(
                name=zip_filename,
                content=zip_buffer.getvalue(),
                content_type="application/zip",
            )

            # Delete existing zip if regenerating
            if existing_zip:
                self.stdout.write("  Removing existing zip file")
                existing_zip.delete()

            # Create File object for the zip
            zip_file_obj = File(
                content_object=album,
                type=File.PRIVATE,  # Keep zip files private like individual photos
                description=f"Complete photo collection for {album.title}",
                tags=["gallery:collection", "type:zip"],
                file=zip_uploaded_file,
            )
            zip_file_obj.save()

            self.stdout.write(self.style.SUCCESS(f"  Successfully created zip file: {zip_file_obj.file.name}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to create zip file for album '{album.title}': {str(e)}"))
