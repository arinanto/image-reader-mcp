"""Image processing utilities"""
import io
import re
import requests
from PIL import Image as PILImage
from mcp.server.fastmcp import Image

_SIZE_PATTERN = re.compile(r"^(\d+)x(\d+)$")


def _pil_to_image(img: PILImage) -> Image:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    return Image(data=img_bytes, format='png')


def _parse_image_size(image_size: str) -> tuple[int, int]:
    """Parse and validate a "WIDTHxHEIGHT" size string.

    Args:
        image_size: Size in the form "WIDTHxHEIGHT" (e.g. "256x128")

    Returns:
        (width, height) tuple of positive integers

    Raises:
        ValueError: If the string is not in the form "WIDTHxHEIGHT" or any
            dimension is not a positive integer.
    """
    if not isinstance(image_size, str):
        raise ValueError(
            f"image_size must be a string in the form \"WIDTHxHEIGHT\", got {type(image_size).__name__}"
        )
    match = _SIZE_PATTERN.match(image_size.strip())
    if not match:
        raise ValueError(
            f"Invalid image_size {image_size!r}: expected \"WIDTHxHEIGHT\", e.g. \"128x128\""
        )
    width, height = int(match.group(1)), int(match.group(2))
    if width < 1 or height < 1:
        raise ValueError(
            f"Invalid image_size {image_size!r}: width and height must be positive integers"
        )
    return width, height


def load_local_image(file_path: str, image_size: str = "128x128") -> Image:
    """Load image from local file path"""
    width, height = _parse_image_size(image_size)
    img = PILImage.open(file_path)
    img.load()  # Force-decode now so corrupt files fail early with a clear error
    img = img.resize((width, height))
    return _pil_to_image(img)


def load_remote_image(url: str, timeout: int = 30, image_size: str = "128x128") -> Image:
    """Load image from remote URL"""
    width, height = _parse_image_size(image_size)
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
    img = img.resize((width, height))
    return _pil_to_image(img)
