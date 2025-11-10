from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from users.common.files import (
    DEFAULT_MAX_DIMENSION,
    DETAIL_MAX_DIMENSION,
    compress_if_image,
)


def _generate_image(
    size=(3200, 2400),
    color=(200, 10, 10),
    fmt="JPEG",
    quality=95,
) -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format=fmt, quality=quality)
    return SimpleUploadedFile("photo.jpg", buffer.getvalue(), content_type="image/jpeg")


class CompressIfImageTests(SimpleTestCase):
    def test_reduces_size_and_converts_format(self):
        upload = _generate_image()
        original_size = upload.size

        result = compress_if_image(upload)

        self.assertTrue(result.optimized)
        self.assertLess(result.file.size, original_size)
        self.assertTrue(result.file.name.endswith(".webp"))

        result.file.seek(0)
        with Image.open(result.file) as optimized:
            self.assertLessEqual(max(optimized.size), DEFAULT_MAX_DIMENSION)

    def test_respects_detail_mode(self):
        upload = _generate_image(size=(4000, 4000))
        result = compress_if_image(upload, prefer_detail=True)

        result.file.seek(0)
        with Image.open(result.file) as optimized:
            self.assertLessEqual(max(optimized.size), DETAIL_MAX_DIMENSION)

    def test_skips_non_images(self):
        payload = SimpleUploadedFile("notes.txt", b"not-an-image", content_type="text/plain")
        result = compress_if_image(payload)

        self.assertFalse(result.optimized)
        self.assertIs(result.file, payload)
