"""Management command to bulk upload photos to an album."""

import re
from pathlib import Path
from typing import Any

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError, CommandParser

from evan.models import Album, Event, File
from evan.services.image_processor import ImageProcessor


class Command(BaseCommand):
    """Management command to bulk upload photos to an album."""

    help = "Bulk upload photos to an album"

    def natural_sort_key(self, filename: str) -> list[int | str]:
        """Generate a sort key for natural sorting of filenames with numbers.

        :param filename: The filename to generate a sort key for.
        :returns: A list of strings and integers for natural sorting.
        """
        parts = re.split(r"(\d+)", filename)
        return [int(part) if part.isdigit() else part for part in parts]

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("event_code", type=str, help="Event code")
        parser.add_argument("album_title", type=str, help="Album title")
        parser.add_argument("photos_path", type=str, help="Path to directory containing photos")
        parser.add_argument(
            "--extensions",
            type=str,
            default="jpg,jpeg,png,gif,webp",
            help="Comma-separated list of file extensions to include (default: jpg,jpeg,png,gif,webp)",
        )
        parser.add_argument(
            "--thumbnail-size",
            type=int,
            default=512,
            help="Size for square thumbnails (default: 512)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be uploaded without actually doing it",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        event_code = options["event_code"]
        album_title = options["album_title"]
        photos_path = options["photos_path"]
        extensions = [ext.strip().lower() for ext in options["extensions"].split(",")]
        thumbnail_size = options["thumbnail_size"]
        dry_run = options["dry_run"]

        # Validate event exists
        try:
            event = Event.objects.get(code=event_code)
        except Event.DoesNotExist as exc:
            raise CommandError(f"Event with code '{event_code}' does not exist") from exc

        # Validate photos directory exists
        photos_dir = Path(photos_path)
        if not photos_dir.exists():
            raise CommandError(f"Directory '{photos_path}' does not exist")

        if not photos_dir.is_dir():
            raise CommandError(f"'{photos_path}' is not a directory")

        # Find all photo files
        photo_files = []
        for file_path in photos_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower().lstrip(".") in extensions:
                photo_files.append(file_path)

        if not photo_files:
            self.stdout.write(
                self.style.WARNING(f"No photo files found in '{photos_path}' with extensions: {extensions}")
            )
            return

        photo_files.sort(key=lambda f: self.natural_sort_key(f.name))  # Natural sort for proper numeric ordering

        self.stdout.write(f"Found {len(photo_files)} photo files")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No files will be uploaded"))

        # Get or create album
        album, created = Album.objects.get_or_create(
            event=event,
            title=album_title,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created new album: {album_title}"))
        else:
            self.stdout.write(f"Using existing album: {album_title}")

        if dry_run:
            for photo_file in photo_files:
                self.stdout.write(f"Would upload: {photo_file.name}")
            return

        # Upload photos
        uploaded_count = 0
        for photo_file in photo_files:
            try:
                with open(photo_file, "rb") as f:
                    file_content = f.read()

                # Create uploaded file for original
                original_uploaded_file = SimpleUploadedFile(
                    name=photo_file.name,
                    content=file_content,
                    content_type=f"image/{photo_file.suffix.lower().lstrip('.')}",
                )

                # Create File object for original (no processing tags)
                original_file = File(
                    content_object=album,
                    type=File.PRIVATE,
                    description=photo_file.stem,
                    tags=["gallery:original"],  # Tag to identify as original photo
                    file=original_uploaded_file,
                )
                original_file.save()

                # Create thumbnail version
                # We need to create a fresh uploaded file for the thumbnail since the original is consumed
                thumbnail_uploaded_file = SimpleUploadedFile(
                    name=photo_file.name,
                    content=file_content,
                    content_type=f"image/{photo_file.suffix.lower().lstrip('.')}",
                )

                # Process the thumbnail
                processed_thumbnail = ImageProcessor.process_image(
                    thumbnail_uploaded_file, [f"_process:square_{thumbnail_size}"]
                )

                # Create File object for thumbnail
                thumbnail_file = File(
                    content_object=album,
                    type=File.PRIVATE,
                    description=f"{photo_file.stem} (thumbnail)",
                    tags=[
                        "gallery:thumbnail",
                        f"original_id:{original_file.id}",  # type: ignore  # Link back to original
                        f"size:{thumbnail_size}",  # Record thumbnail size
                    ],
                    file=processed_thumbnail,
                )
                thumbnail_file.save()

                # Update original file to link to thumbnail
                original_file.tags.append(f"thumbnail_id:{thumbnail_file.id}")  # type: ignore
                original_file.save()

                uploaded_count += 1
                self.stdout.write(f"Uploaded: {photo_file.name} (original + thumbnail)")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to upload {photo_file.name}: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully uploaded {uploaded_count} photos (with thumbnails) to album '{album_title}'"
            )
        )
