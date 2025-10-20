"""Image processing utilities"""
import io
import requests
from PIL import Image as PILImage
from mcp.server.fastmcp import Image


def _pil_to_image(img: PILImage) -> Image:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    return Image(data=img_bytes, format='png')


def load_local_image(file_path: str, image_size: str = "128x128") -> Image:
    """Load image from local file path"""
    img = PILImage.open(file_path)
    width, height = map(int, image_size.split('x'))
    img = img.resize((width, height))
    return _pil_to_image(img)


def load_remote_image(url: str, timeout: int = 30, image_size: str = "128x128") -> Image:
    """Load image from remote URL"""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    
    img = PILImage.open(io.BytesIO(response.content))
    width, height = map(int, image_size.split('x'))
    img = img.resize((width, height))
    return _pil_to_image(img)
