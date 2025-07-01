"""Image processing service for optimizing uploaded images."""

import io
import os
from dataclasses import dataclass

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps


@dataclass
class ProcessingInstruction:
    """Represents a parsed processing instruction from tags.

    Examples of supported tag formats and their effects:

    Basic Operations:
    - `_process:square_512` → Center crop to square, resize to 512x512px
    - `_process:resize_800` → Resize maintaining aspect ratio, max dimension 800px
    - `_process:resize_1200x600` → Resize to fit within 1200x600px bounds

    With Quality Modifiers:
    - `_process:square_512:q90` → Square crop + high quality (90%)
    - `_process:resize_800:q60` → Resize + lower quality for smaller files

    With Format Modifiers:
    - `_process:square_512:jpeg` → Square crop + output as JPEG instead of WebP
    - `_process:resize_800:png` → Resize + output as PNG (lossless)
    - `_process:square_256:webp` → Square crop + explicit WebP output

    Combined Modifiers:
    - `_process:square_512:q85:jpeg` → Square crop + 85% quality JPEG
    - `_process:resize_1200:q75:webp` → Resize + 75% quality WebP

    Use Cases:
    - Keynote avatars: `_process:square_512` (perfect squares for profile pics)
    - Thumbnails: `_process:square_256:q70` (small, efficient squares)
    - Hero images: `_process:resize_1200:q85` (large, high-quality)
    - Gallery images: `_process:resize_800` (balanced size/quality)
    """

    operation: str  # 'square', 'resize', etc.
    size: int  # target size
    width: int | None = None  # for fit operations
    height: int | None = None  # for fit operations
    quality: int | None = None  # quality override (1-100)
    format: str | None = None  # output format override ('jpeg', 'png', 'webp')


class ImageProcessor:
    """Service for processing and optimizing images."""

    # Supported image formats for processing
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

    # Maximum dimensions for general images
    MAX_DIMENSIONS = {
        "general": (1200, 800),  # For general images without processing tags
    }

    # Quality settings
    JPEG_QUALITY = 85
    WEBP_QUALITY = 80  # WebP can achieve better quality at lower values
    PNG_OPTIMIZE = True

    @classmethod
    def should_process_image(cls, filename: str, tags: list[str]) -> bool:
        """Check if an image should be processed based on filename and tags.

        Only images with _process: tags should be processed in the new tag-based system.
        """
        if not filename:
            return False

        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in cls.SUPPORTED_FORMATS:
            return False

        return cls._has_processing_tags(tags)

    @classmethod
    def _has_processing_tags(cls, tags: list[str]) -> bool:
        """Check if tags contain processing instructions."""
        return any(tag.startswith("_process:") for tag in tags)

    @classmethod
    def _parse_processing_tags(cls, tags: list[str]) -> list[ProcessingInstruction]:
        """Parse processing instructions from tags."""
        instructions = []

        for tag in tags:
            if not tag.startswith("_process:"):
                continue

            # Parse tag format: _process:operation_size[:modifiers]
            # Examples: _process:square_512, _process:resize_800, _process:square_512:q80, _process:resize_1200:png
            tag_content = tag[9:]  # Remove "_process:" prefix

            # Split by colon to separate base instruction from modifiers
            colon_parts = tag_content.split(":")
            base_instruction = colon_parts[0]
            modifiers = colon_parts[1:] if len(colon_parts) > 1 else []

            # Parse base instruction (operation_size)
            parts = base_instruction.split("_")
            if len(parts) < 2:
                continue  # Invalid format

            operation = parts[0]

            try:
                # Parse size (could be single number or WxH)
                size_str = parts[1]
                if "x" in size_str:
                    # Format like "1200x800"
                    width_str, height_str = size_str.split("x")
                    width, height = int(width_str), int(height_str)
                    size = max(width, height)  # Use larger dimension as primary size
                    instruction = ProcessingInstruction(operation=operation, size=size, width=width, height=height)
                else:
                    # Format like "512"
                    size = int(size_str)
                    instruction = ProcessingInstruction(operation=operation, size=size)

                # Parse optional modifiers
                for modifier in modifiers:
                    if modifier.startswith("q") and modifier[1:].isdigit():
                        # Quality modifier: q85
                        instruction.quality = int(modifier[1:])
                    elif modifier in ["jpg", "jpeg", "png", "webp"]:
                        # Format modifier
                        instruction.format = modifier

                instructions.append(instruction)

            except (ValueError, IndexError):
                # Skip invalid tags
                continue

        return instructions

    @classmethod
    def get_target_dimensions(cls, tags: list[str]) -> tuple[int, int]:
        """Get target dimensions based on image tags."""
        instructions = cls._parse_processing_tags(tags)
        if instructions:
            # Use the first processing instruction
            instruction = instructions[0]
            if instruction.width and instruction.height:
                return instruction.width, instruction.height
            else:
                return instruction.size, instruction.size

        # Default to general dimensions
        return cls.MAX_DIMENSIONS["general"]

    @classmethod
    def _apply_square_crop(cls, image: Image.Image, target_size: int) -> Image.Image:
        """Crop image to square from center, then resize to target size."""
        width, height = image.size

        # Determine crop size (smallest dimension)
        crop_size = min(width, height)

        # Calculate crop coordinates (center crop)
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        right = left + crop_size
        bottom = top + crop_size

        # Crop to square
        square_image = image.crop((left, top, right, bottom))

        # Resize to target
        return square_image.resize((target_size, target_size), Image.Resampling.LANCZOS)

    @classmethod
    def _apply_resize(cls, image: Image.Image, max_size: int) -> Image.Image:
        """Resize image maintaining aspect ratio, with max dimension as max_size."""
        width, height = image.size

        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            # Landscape
            new_width = min(width, max_size)
            new_height = int((height * new_width) / width)
        else:
            # Portrait or square
            new_height = min(height, max_size)
            new_width = int((width * new_height) / height)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @classmethod
    def process_image(cls, uploaded_file: InMemoryUploadedFile, tags: list[str]) -> InMemoryUploadedFile:
        """
        Process and optimize an uploaded image.

        :param uploaded_file: The original uploaded image file
        :param tags: List of tags to determine processing parameters
        :returns: Optimized image file
        """
        if not cls.should_process_image(uploaded_file.name, tags):
            return uploaded_file

        try:
            # Open the image
            image = Image.open(uploaded_file)

            # Handle orientation based on EXIF data
            image = ImageOps.exif_transpose(image)

            # Convert RGBA to RGB for JPEG output (handles transparency)
            if image.mode in ("RGBA", "LA", "P"):
                # Create white background for transparent images
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if len(image.split()) > 3 else None)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # Apply processing based on tags
            processed_image = cls._apply_tag_based_processing(image, tags)

            # Save optimized image to memory
            output_buffer = io.BytesIO()

            # Determine output format and quality
            output_format, quality, file_ext = cls._get_output_settings(tags)

            # Save the image
            if output_format == "JPEG":
                processed_image.save(
                    output_buffer, format=output_format, quality=quality, optimize=True, progressive=True
                )
            elif output_format == "WEBP":
                processed_image.save(output_buffer, format=output_format, quality=quality, optimize=True)
            else:  # PNG
                processed_image.save(output_buffer, format=output_format, optimize=cls.PNG_OPTIMIZE)

            # Create new filename with appropriate extension
            original_name = uploaded_file.name
            name_without_ext = os.path.splitext(original_name)[0]
            new_filename = f"{name_without_ext}.{file_ext}"

            # Create new InMemoryUploadedFile
            output_buffer.seek(0)
            processed_file = InMemoryUploadedFile(
                output_buffer,
                "ImageField",
                new_filename,
                f"image/{output_format.lower()}",
                output_buffer.getbuffer().nbytes,
                None,
            )

            return processed_file

        except Exception as e:
            # If processing fails, return original file
            # Log the error in production
            print(f"Error processing image {uploaded_file.name}: {e}")
            return uploaded_file

    @classmethod
    def _apply_tag_based_processing(cls, image: Image.Image, tags: list[str]) -> Image.Image:
        """Apply processing operations based on tags."""
        instructions = cls._parse_processing_tags(tags)

        if instructions:
            # Use the first processing instruction
            instruction = instructions[0]

            if instruction.operation == "square":
                return cls._apply_square_crop(image, instruction.size)
            elif instruction.operation == "resize":
                return cls._apply_resize(image, instruction.size)
            # Add more operations here as needed

        # No processing instructions, apply general optimization only
        max_width, max_height = cls.get_target_dimensions(tags)
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        return image

    @classmethod
    def _get_output_settings(cls, tags: list[str]) -> tuple[str, int, str]:
        """Get output format, quality, and file extension based on tags."""
        instructions = cls._parse_processing_tags(tags)

        # Check for format/quality overrides in processing tags
        output_format = "WEBP"  # Default to WebP for better compression
        quality = cls.WEBP_QUALITY  # Default

        if instructions:
            instruction = instructions[0]
            if instruction.format:
                if instruction.format.lower() in ["jpg", "jpeg"]:
                    output_format = "JPEG"
                    quality = cls.JPEG_QUALITY
                elif instruction.format.lower() == "png":
                    output_format = "PNG"
                elif instruction.format.lower() == "webp":
                    output_format = "WEBP"
                    quality = cls.WEBP_QUALITY

            if instruction.quality:
                quality = instruction.quality

        # Map format to file extension
        file_ext = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}.get(output_format, "webp")

        return output_format, quality, file_ext

    @classmethod
    def estimate_file_reduction(cls, original_size: int, tags: list[str]) -> dict:
        """
        Estimate potential file size reduction for reporting.

        :param original_size: Original file size in bytes
        :param tags: List of tags to determine processing type
        :returns: Dictionary with estimated savings
        """
        instructions = cls._parse_processing_tags(tags)
        if instructions:
            instruction = instructions[0]
            # Square operations typically see higher reduction due to cropping + resizing
            estimated_reduction = 0.7 if instruction.operation == "square" else 0.5
        else:
            # General optimization only
            estimated_reduction = 0.5

        new_size = int(original_size * (1 - estimated_reduction))
        savings = original_size - new_size

        return {
            "original_size": original_size,
            "estimated_new_size": new_size,
            "estimated_savings_bytes": savings,
            "estimated_reduction_percent": int(estimated_reduction * 100),
        }
