"""
Utilidades para manejo de archivos (procesamiento y compresión de imágenes).
"""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, cast

from django.core.files.base import ContentFile, File
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = None  # confiamos en límites de tamaño previos (<10 MB)

DEFAULT_MAX_DIMENSION = 1920
DETAIL_MAX_DIMENSION = 2560
DEFAULT_QUALITY = 80
SUPPORTED_TARGET_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}


class ImageCompressionResult:
    """Agrupa datos útiles tras intentar comprimir un archivo."""

    def __init__(self, file: File | UploadedFile, optimized: bool):
        self.file = file
        self.optimized = optimized


def _reset_stream(stream: BinaryIO | File[Any] | UploadedFile | BytesIO) -> None:
    if hasattr(stream, "seek"):
        stream.seek(0, os.SEEK_SET)


def _read_bytes(upload: UploadedFile | File[Any]) -> bytes:
    """Lee el archivo completo (<=10 MB) y resetea el puntero."""
    _reset_stream(upload)
    data = cast(bytes, upload.read())
    _reset_stream(upload)
    return data


def _choose_format(image: Image.Image, preferred: str | None) -> str:
    has_alpha = "A" in image.getbands()
    preferred_fmt = (preferred or "").upper()

    if preferred_fmt and preferred_fmt in SUPPORTED_TARGET_FORMATS:
        if preferred_fmt == "JPEG" and has_alpha:
            return "WEBP"
        return "JPEG" if preferred_fmt == "JPG" else preferred_fmt

    # Por defecto usamos WEBP para mejor compresión; JPEG si no hay alpha
    if not has_alpha:
        return "WEBP"
    return "WEBP"


def _build_new_name(original_name: str, fmt: str) -> str:
    base = Path(original_name).stem or "upload"
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    return f"{base}.{ext}"


def _save_image(image: Image.Image, fmt: str, *, quality: int) -> bytes:
    buffer = BytesIO()
    save_kwargs: dict = {"format": fmt}

    if fmt == "JPEG":
        image = image.convert("RGB")
        save_kwargs.update({"quality": quality, "optimize": True, "progressive": True})
    elif fmt == "WEBP":
        mode = "RGBA" if "A" in image.getbands() else "RGB"
        image = image.convert(mode)
        save_kwargs.update({"quality": quality, "method": 6})
    elif fmt == "PNG":
        save_kwargs.update({"optimize": True, "compress_level": 6})
    else:
        save_kwargs.update({"quality": quality})

    image.save(buffer, **save_kwargs)
    return buffer.getvalue()


def compress_if_image(
    uploaded_file: UploadedFile | File,
    *,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
    detail_max_dimension: int = DETAIL_MAX_DIMENSION,
    prefer_detail: bool = False,
    quality: int = DEFAULT_QUALITY,
    preferred_format: str | None = None,
) -> ImageCompressionResult:
    """
    Si el archivo es una imagen, la comprime/redimensiona y devuelve un ContentFile.
    Caso contrario, retorna el archivo original.
    """

    if not uploaded_file:
        raise ValueError("uploaded_file es requerido")

    original_bytes = _read_bytes(uploaded_file)
    try:
        image = cast(Image.Image, Image.open(BytesIO(original_bytes)))
    except UnidentifiedImageError:
        _reset_stream(uploaded_file)
        return ImageCompressionResult(uploaded_file, optimized=False)

    transposed = ImageOps.exif_transpose(image)
    if transposed is not None:
        image = transposed
    target_dimension = detail_max_dimension if prefer_detail else max_dimension
    image.thumbnail((target_dimension, target_dimension), Image.Resampling.LANCZOS)

    fmt = _choose_format(image, preferred_format)
    optimized_bytes = _save_image(image, fmt, quality=quality)

    # Si no ganamos nada, devolvemos el archivo original
    if len(optimized_bytes) >= len(original_bytes):
        _reset_stream(uploaded_file)
        return ImageCompressionResult(uploaded_file, optimized=False)

    new_name = _build_new_name(uploaded_file.name or "upload", fmt)
    optimized_file = ContentFile(optimized_bytes, name=new_name)
    return ImageCompressionResult(optimized_file, optimized=True)
