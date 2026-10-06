"""Image processing utilities"""
import io
import os
from collections.abc import Iterable
from pathlib import Path

import requests
from PIL import Image as PILImage
from mcp.server.fastmcp import Image

# Largest dimension (in pixels) an image may have after processing. Images whose
# longest side exceeds this are scaled down proportionally; smaller images are
# returned unchanged.
DEFAULT_MAX_IMAGE_DIMENSION = 1600


def resolve_directory(directory: str | os.PathLike[str]) -> Path:
    """Resolve a directory to an absolute, symlink-free path.

    ``~`` and environment variables are expanded before resolution.
    """
    return Path(os.path.expandvars(os.fspath(directory))).expanduser().resolve()


def is_path_allowed(
    file_path: str | os.PathLike[str], allowed_directories: Iterable[str | os.PathLike[str]]
) -> bool:
    """Return True if ``file_path`` lives inside one of ``allowed_directories``.

    Both sides are fully resolved first, so ``..`` traversal and symlinks that
    point outside an allowed directory are rejected.
    """
    resolved = Path(os.path.expandvars(os.fspath(file_path))).expanduser().resolve()
    for directory in allowed_directories:
        root = resolve_directory(directory)
        if resolved == root or root in resolved.parents:
            return True
    return False


def assert_path_allowed(
    file_path: str | os.PathLike[str], allowed_directories: Iterable[str | os.PathLike[str]]
) -> None:
    """Raise PermissionError if ``file_path`` is outside every allowed directory.

    The error message lists the allowed directories so clients can correct the
    call. An empty allowlist denies every path.
    """
    directories = list(allowed_directories)
    if is_path_allowed(file_path, directories):
        return
    allowed = ", ".join(str(resolve_directory(d)) for d in directories) or "(none configured)"
    raise PermissionError(
        f"Access to {os.fspath(file_path)!r} is forbidden: it is outside the allowed "
        f"directories. Allowed directories: {allowed}"
    )


def _pil_to_image(img: PILImage) -> Image:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    return Image(data=img_bytes, format='png')


def _validate_max_dimension(max_dimension: int) -> int:
    """Validate and return ``max_dimension`` as a positive integer.

    Args:
        max_dimension: Largest allowed image dimension in pixels.

    Returns:
        The validated dimension.

    Raises:
        ValueError: If ``max_dimension`` is not a positive integer.
    """
    if isinstance(max_dimension, bool) or not isinstance(max_dimension, int) or max_dimension < 1:
        raise ValueError(f"max_dimension must be a positive integer, got {max_dimension!r}")
    return max_dimension


def load_local_image(
    file_path: str, max_dimension: int = DEFAULT_MAX_IMAGE_DIMENSION
) -> Image:
    """Load an image from a local file path, capped to ``max_dimension``.

    The longest side is scaled down to ``max_dimension`` while preserving the
    aspect ratio; images already within the limit are returned unchanged.
    """
    dimension = _validate_max_dimension(max_dimension)
    img = PILImage.open(file_path)
    img.load()  # Force-decode now so corrupt files fail early with a clear error
    img.thumbnail((dimension, dimension), PILImage.LANCZOS)
    return _pil_to_image(img)


def load_remote_image(
    url: str, timeout: int = 30, max_dimension: int = DEFAULT_MAX_IMAGE_DIMENSION
) -> Image:
    """Load an image from a remote URL, capped to ``max_dimension``.

    The longest side is scaled down to ``max_dimension`` while preserving the
    aspect ratio; images already within the limit are returned unchanged.
    """
    dimension = _validate_max_dimension(max_dimension)
    if timeout <= 0:
        raise ValueError(f"timeout must be a positive number, got {timeout}")
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError(f"URL must use the http or https scheme, got {url!r}")

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type and not content_type.startswith("image/"):
        raise ValueError(
            f"Expected an image but {url} returned Content-Type {content_type!r}"
        )

    img = PILImage.open(io.BytesIO(response.content))
    img.load()  # Force-decode now so non-image payloads fail early
    img.thumbnail((dimension, dimension), PILImage.LANCZOS)
    return _pil_to_image(img)
