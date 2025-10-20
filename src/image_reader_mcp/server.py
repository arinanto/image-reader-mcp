"""Image Reader MCP Server"""
import os
from mcp.server.fastmcp import FastMCP, Image
from image_reader_mcp.image_utils import load_local_image, load_remote_image

# Create FastMCP server
mcp = FastMCP("Image Reader")


@mcp.tool()
def read_local_image(file_path: str, image_size: str = "128x128") -> Image:
    """Read and return an image from a local file path.
    
    Args:
        file_path: Absolute path to the local image file
        image_size: Size to resize image to in format "WIDTHxHEIGHT" (default: "128x128")
        
    Returns:
        Image object with the loaded and resized image data
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file not found: {file_path}")
    
    return load_local_image(file_path, image_size)


@mcp.tool()
def read_remote_image(url: str, timeout: int = 30, image_size: str = "128x128") -> Image:
    """Read and return an image from a remote URL.
    
    Args:
        url: URL of the remote image
        timeout: Request timeout in seconds (default: 30)
        image_size: Size to resize image to in format "WIDTHxHEIGHT" (default: "128x128")
        
    Returns:
        Image object with the loaded and resized image data
    """
    return load_remote_image(url, timeout, image_size)


def main():
    """Main entry point for the MCP server"""
    mcp.run()
