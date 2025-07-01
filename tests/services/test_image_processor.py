"""Tests for image processing functionality."""

import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

from evan.services.image_processor import ImageProcessor


class TestImageProcessor:
    """Test cases for the ImageProcessor service."""

    def create_test_image(self, format="JPEG", size=(800, 600), mode="RGB"):
        """Create a test image for processing."""
        image = Image.new(mode, size, color="red")
        buffer = io.BytesIO()
        image.save(buffer, format=format, quality=95)
        buffer.seek(0)

        filename = f"test_image.{format.lower()}"
        if format == "JPEG":
            filename = "test_image.jpg"

        return InMemoryUploadedFile(
            buffer, "ImageField", filename, f"image/{format.lower()}", buffer.getbuffer().nbytes, None
        )

    def test_should_process_image_formats(self):
        """Test that only images with _process: tags are marked for processing."""
        # Should NOT process images without _process: tags
        assert not ImageProcessor.should_process_image("avatar.jpg", ["_internal:avatar"])
        assert not ImageProcessor.should_process_image("photo.png", [])
        assert not ImageProcessor.should_process_image("image.jpg", ["other:tag"])

        # Should process images with _process: tags
        assert ImageProcessor.should_process_image("photo.png", ["_process:square_512"])
        assert ImageProcessor.should_process_image("image.jpg", ["_process:resize_800"])

        # Should NOT process unsupported formats regardless of tags
        assert not ImageProcessor.should_process_image("document.pdf", ["_process:square_512"])
        assert not ImageProcessor.should_process_image("document.txt", ["_process:resize_800"])

    def test_should_process_general_image(self):
        """Test that general images without _process: tags are NOT processed."""
        assert not ImageProcessor.should_process_image("photo.jpg", [])
        assert not ImageProcessor.should_process_image("image.png", ["other:tag"])
        assert not ImageProcessor.should_process_image("avatar.jpg", ["_internal:avatar"])
        assert not ImageProcessor.should_process_image("document.txt", [])

    def test_get_target_dimensions_with_processing_tags(self):
        """Test getting target dimensions with processing tags."""
        dimensions = ImageProcessor.get_target_dimensions(["_process:square_512"])
        assert dimensions == (512, 512)

    def test_get_target_dimensions_fallback(self):
        """Test getting target dimensions fallback for tags without _process:."""
        # This method still returns fallback dimensions for backward compatibility
        # in case it's called without _process: tags, but processing won't happen
        dimensions = ImageProcessor.get_target_dimensions([])
        assert dimensions == (1200, 800)

    def test_process_large_image_with_processing_tags(self):
        """Test that large images are resized with _process: tags."""
        # Create a large test image
        test_file = self.create_test_image(size=(2000, 1500))

        # Process with specific processing tags
        processed = ImageProcessor.process_image(test_file, ["_process:resize_800"])

        # Verify processing occurred (now defaults to WebP)
        assert processed.name.endswith(".webp")
        assert processed.size < test_file.size  # Should be smaller

        # Verify dimensions by reading the processed image
        processed.seek(0)
        processed_image = Image.open(processed)
        assert processed_image.width <= 800  # resize_800 max width
        assert processed_image.height <= 800  # resize_800 max height

    def test_process_image_without_processing_tags(self):
        """Test that images without _process: tags are NOT processed."""
        # Create a test image
        test_file = self.create_test_image(size=(2000, 1500))
        original_name = test_file.name
        original_size = test_file.size

        # Process without _process: tags - should return original file
        processed = ImageProcessor.process_image(test_file, [])

        # Should be the same file (no processing)
        assert processed is test_file
        assert processed.name == original_name
        assert processed.size == original_size

        # Test with other non-_process: tags
        processed2 = ImageProcessor.process_image(test_file, ["_internal:avatar"])
        assert processed2 is test_file

    def test_process_small_image_with_processing_tags(self):
        """Test that small images are still processed when using _process: tags."""
        # Create a small test image
        test_file = self.create_test_image(size=(200, 150))

        # Process with processing tags
        processed = ImageProcessor.process_image(test_file, ["_process:square_256"])

        # Should be processed to a 256x256 square
        processed.seek(0)
        processed_image = Image.open(processed)
        assert processed_image.width == 256
        assert processed_image.height == 256

    def test_process_png_to_webp(self):
        """Test that PNG images are converted to WebP (new default)."""
        # Create a PNG test image
        test_file = self.create_test_image(format="PNG", size=(500, 400))

        # Process the image with _process: tags
        processed = ImageProcessor.process_image(test_file, ["_process:resize_400"])

        # Should be converted to WebP (new default)
        assert processed.name.endswith(".webp")
        assert processed.content_type == "image/webp"

    def test_process_explicit_jpeg_format(self):
        """Test that we can explicitly request JPEG format."""
        # Create a test image
        test_file = self.create_test_image(format="PNG", size=(500, 400))

        # Process with explicit JPEG format request
        processed = ImageProcessor.process_image(test_file, ["_process:square_512:jpeg"])

        # Should be converted to JPEG as requested
        assert processed.name.endswith(".jpg")
        assert processed.content_type == "image/jpeg"

    def test_process_non_image_file(self):
        """Test that non-image files are not processed."""
        # Create a mock non-image file
        buffer = io.BytesIO(b"This is not an image")
        text_file = InMemoryUploadedFile(
            buffer, "FileField", "document.txt", "text/plain", len(b"This is not an image"), None
        )

        # Should return the original file unchanged
        processed = ImageProcessor.process_image(text_file, [])
        assert processed == text_file

    def test_estimate_file_reduction_fallback(self):
        """Test file reduction estimation fallback for images without _process: tags."""
        original_size = 2000000  # 2MB
        estimate = ImageProcessor.estimate_file_reduction(original_size, [])

        assert estimate["original_size"] == original_size
        assert estimate["estimated_reduction_percent"] == 50
        assert estimate["estimated_savings_bytes"] == 1000000

    def test_process_with_transparency(self):
        """Test processing images with transparency using _process: tags."""
        # Create a PNG with transparency
        test_file = self.create_test_image(format="PNG", size=(300, 200), mode="RGBA")

        # Process the image with a _process: tag
        processed = ImageProcessor.process_image(test_file, ["_process:resize_200"])

        # Should be converted to WebP (new default)
        assert processed.name.endswith(".webp")

        # Verify no transparency in result (WebP with RGB mode)
        processed.seek(0)
        processed_image = Image.open(processed)
        assert processed_image.mode == "RGB"

    # Tag-based processing tests

    def test_parse_processing_tags_square(self):
        """Test parsing square crop processing tags."""
        tags = ["_internal:avatar", "_process:square_512", "other:tag"]
        instructions = ImageProcessor._parse_processing_tags(tags)

        assert len(instructions) == 1
        assert instructions[0].operation == "square"
        assert instructions[0].size == 512
        assert instructions[0].width is None
        assert instructions[0].height is None

    def test_parse_processing_tags_resize(self):
        """Test parsing resize processing tags."""
        tags = ["_process:resize_800", "other:tag"]
        instructions = ImageProcessor._parse_processing_tags(tags)

        assert len(instructions) == 1
        assert instructions[0].operation == "resize"
        assert instructions[0].size == 800

    def test_parse_processing_tags_with_quality(self):
        """Test parsing processing tags with quality modifier."""
        tags = ["_process:square_512:q80"]
        instructions = ImageProcessor._parse_processing_tags(tags)

        assert len(instructions) == 1
        assert instructions[0].operation == "square"
        assert instructions[0].size == 512
        assert instructions[0].quality == 80

    def test_parse_processing_tags_with_format(self):
        """Test parsing processing tags with format modifier."""
        tags = ["_process:resize_1200:png"]
        instructions = ImageProcessor._parse_processing_tags(tags)

        assert len(instructions) == 1
        assert instructions[0].operation == "resize"
        assert instructions[0].size == 1200
        assert instructions[0].format == "png"

    def test_parse_processing_tags_multiple(self):
        """Test parsing multiple processing tags (first one should be used)."""
        tags = ["_process:square_512", "_process:resize_800"]
        instructions = ImageProcessor._parse_processing_tags(tags)

        assert len(instructions) == 2
        assert instructions[0].operation == "square"
        assert instructions[0].size == 512
        assert instructions[1].operation == "resize"
        assert instructions[1].size == 800

    def test_parse_processing_tags_invalid(self):
        """Test parsing invalid processing tags."""
        tags = ["_process:invalid", "_process:", "_process:square", "not_process:tag"]
        instructions = ImageProcessor._parse_processing_tags(tags)

        assert len(instructions) == 0

    def test_has_processing_tags(self):
        """Test checking for presence of processing tags."""
        assert ImageProcessor._has_processing_tags(["_process:square_512"])
        assert ImageProcessor._has_processing_tags(["other:tag", "_process:resize_800"])
        assert not ImageProcessor._has_processing_tags(["_internal:avatar"])
        assert not ImageProcessor._has_processing_tags([])

    def test_should_process_image_with_processing_tags(self):
        """Test that images with processing tags are marked for processing."""
        assert ImageProcessor.should_process_image("photo.jpg", ["_process:square_512"])
        assert ImageProcessor.should_process_image("image.png", ["_internal:avatar", "_process:resize_800"])
        assert not ImageProcessor.should_process_image("document.pdf", ["_process:square_512"])

    def test_square_crop_processing(self):
        """Test square crop processing with tag-based system."""
        # Create a rectangular test image
        test_file = self.create_test_image(size=(800, 600))

        # Process with square crop tag
        processed = ImageProcessor.process_image(test_file, ["_process:square_512"])

        # Verify it's a square image of correct size
        processed.seek(0)
        processed_image = Image.open(processed)
        assert processed_image.width == 512
        assert processed_image.height == 512

    def test_resize_processing(self):
        """Test resize processing with tag-based system."""
        # Create a large test image
        test_file = self.create_test_image(size=(1600, 1200))

        # Process with resize tag
        processed = ImageProcessor.process_image(test_file, ["_process:resize_800"])

        # Verify it's resized while maintaining aspect ratio
        processed.seek(0)
        processed_image = Image.open(processed)
        assert max(processed_image.width, processed_image.height) == 800
        # Should maintain aspect ratio (4:3)
        assert processed_image.width == 800
        assert processed_image.height == 600

    def test_keynote_avatar_integration(self):
        """Test the keynote avatar integration with new processing tags."""
        # Create a test image for keynote avatar
        test_file = self.create_test_image(size=(1000, 800))

        # Process with keynote avatar tags (now uses only the processing tag)
        processed = ImageProcessor.process_image(test_file, ["_internal:avatar", "_process:square_512"])

        # Should use the new tag-based processing
        processed.seek(0)
        processed_image = Image.open(processed)
        assert processed_image.width == 512
        assert processed_image.height == 512

    def test_estimate_file_reduction_with_processing_tags(self):
        """Test file reduction estimation with processing tags."""
        original_size = 1000000  # 1MB

        # Test with square processing tag
        estimate = ImageProcessor.estimate_file_reduction(original_size, ["_process:square_512"])
        assert estimate["original_size"] == original_size
        assert estimate["estimated_reduction_percent"] == 70

        # Test with resize processing tag
        estimate = ImageProcessor.estimate_file_reduction(original_size, ["_process:resize_800"])
        assert estimate["original_size"] == original_size
        assert estimate["estimated_reduction_percent"] == 50

        # Test with resize processing tag
        estimate = ImageProcessor.estimate_file_reduction(original_size, ["_process:resize_800"])
        assert estimate["original_size"] == original_size
        assert estimate["estimated_reduction_percent"] == 50
