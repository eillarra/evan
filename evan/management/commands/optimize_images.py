"""Management command to optimize existing images in the database."""

import io
import logging
import os
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q

from evan.models.rel.files import File
from evan.services.image_processor import ImageProcessor


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to optimize existing image files."""

    help = "Optimize existing image files, particularly keynote avatars"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be processed without actually doing it",
        )
        parser.add_argument(
            "--filter-tags",
            type=str,
            help="Comma-separated list of tags to filter files (e.g., '_internal:avatar')",
        )
        parser.add_argument(
            "--max-size",
            type=int,
            default=1048576,  # 1MB
            help="Only process files larger than this size in bytes (default: 1MB)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of files to process in each batch (default: 50)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options["dry_run"]
        filter_tags = options["filter_tags"]
        max_size_bytes = options["max_size"]
        batch_size = options["batch_size"]

        # Build query for image files
        queryset = File.objects.all()

        # Filter by tags if specified, otherwise default to files with _process: tags
        if filter_tags:
            tag_list = [tag.strip() for tag in filter_tags.split(",")]
            tag_conditions = Q()
            for tag in tag_list:
                tag_conditions |= Q(tags__contains=[tag])
            queryset = queryset.filter(tag_conditions)
        else:
            # Default: only process files with _process: tags
            # Since MySQL doesn't have unnest, we'll filter at the application level
            # but first get a reasonable subset by checking for common _process tags
            common_process_tags = [
                "_process:square_512",
                "_process:square_256",
                "_process:square_128",
                "_process:resize_800",
                "_process:resize_1200",
                "_process:resize_400",
            ]
            tag_conditions = Q()
            for tag in common_process_tags:
                tag_conditions |= Q(tags__contains=[tag])
            queryset = queryset.filter(tag_conditions)

        # Filter by file extensions (images only)
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
        file_conditions = Q()
        for ext in image_extensions:
            file_conditions |= Q(file__iendswith=ext)
        queryset = queryset.filter(file_conditions)

        total_files = queryset.count()
        self.stdout.write(f"Found {total_files} image files to potentially process")

        if total_files == 0:
            self.stdout.write("No image files found matching the criteria")
            return

        # Track statistics
        processed_count = 0
        skipped_count = 0
        error_count = 0
        total_original_size = 0
        total_new_size = 0

        # Process files in batches
        for i in range(0, total_files, batch_size):
            batch = queryset[i : i + batch_size]

            for file_obj in batch:
                try:
                    # Get file size
                    file_size = file_obj.file.size

                    # Check if it's an avatar image (more lenient size requirements)
                    is_avatar = any(tag.endswith(":avatar") for tag in file_obj.tags)

                    # Skip small files (but be more lenient with avatars)
                    min_size = max_size_bytes // 5 if is_avatar else max_size_bytes  # 200KB for avatars, 1MB for others

                    if file_size < min_size:
                        skipped_count += 1
                        continue

                    # Check if processing is needed
                    if not ImageProcessor.should_process_image(file_obj.file.name, file_obj.tags):
                        skipped_count += 1
                        continue

                    self.stdout.write(f"Processing: {file_obj.file.name} ({file_size} bytes)")

                    if dry_run:
                        # Just estimate potential savings
                        estimate = ImageProcessor.estimate_file_reduction(file_size, file_obj.tags)
                        self.stdout.write(
                            f"  Would save ~{estimate['estimated_savings_bytes']} bytes "
                            f"({estimate['estimated_reduction_percent']}% reduction)"
                        )
                        total_original_size += estimate["original_size"]
                        total_new_size += estimate["estimated_new_size"]
                    else:
                        # Actually process the image
                        original_file = file_obj.file

                        # Read file content
                        original_file.open()
                        file_content = original_file.read()
                        original_file.close()

                        # Create InMemoryUploadedFile for processing
                        from django.core.files.uploadedfile import InMemoryUploadedFile

                        temp_buffer = io.BytesIO(file_content)
                        temp_uploaded_file = InMemoryUploadedFile(
                            temp_buffer,
                            "ImageField",
                            file_obj.file.name,
                            "image/*",  # Will be detected by PIL
                            len(file_content),
                            None,
                        )

                        # Process the image
                        processed_file = ImageProcessor.process_image(temp_uploaded_file, file_obj.tags)

                        # Save the processed file
                        file_changed = (
                            processed_file.name != temp_uploaded_file.name
                            or processed_file.size != temp_uploaded_file.size
                        )
                        if file_changed:
                            original_size = file_obj.file.size

                            # Use the original file's basename to prevent duplicate hashes
                            # Extract the base name without any existing hash
                            original_name = file_obj.file.name
                            original_base = os.path.basename(original_name)
                            original_dir = os.path.dirname(original_name)

                            # Remove any existing hash pattern (e.g., '_AbC123' before the extension)
                            import re

                            name_without_ext = os.path.splitext(original_base)[0]
                            # Remove hash pattern like '_AbC123' at the end
                            clean_name = re.sub(r"_[A-Za-z0-9]{6,}$", "", name_without_ext)

                            # Get the new extension from the processed file
                            new_ext = os.path.splitext(processed_file.name)[1]

                            # Construct the target filename
                            if original_dir:
                                target_filename = f"{original_dir}/{clean_name}{new_ext}"
                            else:
                                target_filename = f"{clean_name}{new_ext}"

                            # Save with the cleaned filename to avoid duplicates
                            file_obj.file.save(target_filename, processed_file, save=True)
                            new_size = file_obj.file.size
                            savings = original_size - new_size

                            # Update description to reflect new extension if needed
                            original_description = file_obj.description
                            if original_description:
                                # Extract extensions
                                original_ext = os.path.splitext(temp_uploaded_file.name)[1].lower()
                                new_ext = os.path.splitext(processed_file.name)[1].lower()

                                # If extensions differ and description ends with the original extension,
                                # replace it with the new extension
                                if original_ext != new_ext and original_description.lower().endswith(original_ext):
                                    file_obj.description = original_description[: -len(original_ext)] + new_ext
                                    file_obj.save(update_fields=["description"])

                            self.stdout.write(
                                f"  Processed: {original_size} → {new_size} bytes "
                                f"(saved {savings} bytes, {int(savings / original_size * 100)}%)"
                            )

                            total_original_size += original_size
                            total_new_size += new_size
                        else:
                            self.stdout.write("  No optimization needed")
                            skipped_count += 1

                    processed_count += 1

                except Exception as e:
                    error_count += 1
                    self.stderr.write(f"Error processing {file_obj.file.name}: {e}")

            # Progress update
            self.stdout.write(f"Processed batch {i // batch_size + 1}/{(total_files - 1) // batch_size + 1}")

        # Final statistics
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Total files found: {total_files}")
        self.stdout.write(f"Files processed: {processed_count}")
        self.stdout.write(f"Files skipped: {skipped_count}")
        self.stdout.write(f"Errors: {error_count}")

        if processed_count > 0:
            total_savings = total_original_size - total_new_size
            avg_reduction = int(total_savings / total_original_size * 100) if total_original_size > 0 else 0

            self.stdout.write(f"Total original size: {self._format_bytes(total_original_size)}")
            self.stdout.write(f"Total new size: {self._format_bytes(total_new_size)}")
            self.stdout.write(f"Total savings: {self._format_bytes(total_savings)} ({avg_reduction}%)")

            if dry_run:
                self.stdout.write("\nThis was a dry run. Use --no-dry-run to actually process files.")

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format."""
        value = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"
