"""Image Reader MCP Server"""
import argparse
import os
from collections.abc import Iterable, Sequence

from mcp.server.fastmcp import FastMCP, Image

from image_reader_mcp.image_utils import (
    assert_path_allowed,
    load_local_image,
    load_remote_image,
    resolve_directory,
)

# Create FastMCP server
mcp = FastMCP("Image Reader")

# Directories local image reads are restricted to. Populated from the CLI.
_allowed_directories: list[str] = []


def set_allowed_directories(directories: Iterable[str]) -> None:
    """Set the directories that local image reads are restricted to.

    Paths are resolved (absolute, symlinks followed) before being stored.
    """
    global _allowed_directories
    _allowed_directories = [str(resolve_directory(directory)) for directory in directories]


def get_allowed_directories() -> list[str]:
    """Return the resolved directories that local image reads are restricted to."""
    return list(_allowed_directories)


@mcp.tool()
def read_local_image(file_path: str, image_size: str = "128x128") -> Image:
    """Read and return an image from a local file path.

    The path must live inside one of the directories the server was started
    with; any other path is rejected.

    Args:
        file_path: Absolute path to the local image file
        image_size: Size to resize image to in format "WIDTHxHEIGHT" (default: "128x128")

    Returns:
        Image object with the loaded and resized image data
    """
    assert_path_allowed(file_path, _allowed_directories)

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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-reader-mcp",
        description=(
            "Image Reader MCP server. Local image reads are restricted to the "
            "directories passed as arguments."
        ),
    )
    parser.add_argument(
        "directories",
        nargs="*",
        metavar="DIR",
        help=(
            "Directory that local images may be read from. Pass several to allow "
            "multiple directories. If none are given, all local reads are denied."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the MCP server"""
    args = _build_arg_parser().parse_args(argv)
    set_allowed_directories(args.directories)
    mcp.run()
