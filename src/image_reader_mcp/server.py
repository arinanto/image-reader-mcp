"""Image Reader MCP Server"""
import argparse
import os
from collections.abc import Iterable, Sequence

from mcp.server.fastmcp import FastMCP, Image

from image_reader_mcp.image_utils import (
    DEFAULT_MAX_IMAGE_DIMENSION,
    assert_path_allowed,
    load_local_image,
    load_remote_image,
    resolve_directory,
)

# Create FastMCP server
mcp = FastMCP("Image Reader")

# Directories local image reads are restricted to. Populated from the CLI.
_allowed_directories: list[str] = []

# Largest dimension (in pixels) an image may have after processing. Populated
# from the CLI; larger images are scaled down proportionally, smaller ones pass
# through untouched.
_max_image_dimension: int = DEFAULT_MAX_IMAGE_DIMENSION


def set_allowed_directories(directories: Iterable[str]) -> None:
    """Set the directories that local image reads are restricted to.

    Paths are resolved (absolute, symlinks followed) before being stored.
    """
    global _allowed_directories
    _allowed_directories = [str(resolve_directory(directory)) for directory in directories]


def set_max_image_dimension(max_dimension: int) -> None:
    """Set the largest image dimension (in pixels) the tools may return.

    Images whose longest side exceeds this are scaled down proportionally;
    smaller images are returned unchanged.
    """
    global _max_image_dimension
    _max_image_dimension = max_dimension


@mcp.tool()
def list_allowed_directories() -> list[str]:
    """Return the directories the server allows local images to be read from.

    Paths are resolved (absolute, symlinks followed). An empty list means the
    server was started without any directory, so all local reads are denied.

    Returns:
        Resolved absolute paths of the allowed directories.
    """
    return list(_allowed_directories)


@mcp.tool()
def read_local_image(file_path: str) -> Image:
    """Read and return an image from a local file path.

    The path must live inside one of the directories the server was started
    with; any other path is rejected. Images whose longest side exceeds the
    configured maximum dimension are scaled down proportionally.

    Args:
        file_path: Absolute path to the local image file

    Returns:
        Image object with the loaded image data
    """
    assert_path_allowed(file_path, _allowed_directories)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file not found: {file_path}")

    return load_local_image(file_path, _max_image_dimension)


@mcp.tool()
def read_remote_image(url: str, timeout: int = 30) -> Image:
    """Read and return an image from a remote URL.

    Images whose longest side exceeds the configured maximum dimension are
    scaled down proportionally.

    Args:
        url: URL of the remote image
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Image object with the loaded image data
    """
    return load_remote_image(url, timeout, _max_image_dimension)


def _positive_int(value: str) -> int:
    """argparse type for integers that must be at least 1."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return number


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
    parser.add_argument(
        "--max-image-dimension",
        type=_positive_int,
        default=DEFAULT_MAX_IMAGE_DIMENSION,
        metavar="PIXELS",
        help=(
            "Largest image dimension returned, in pixels (default: "
            f"{DEFAULT_MAX_IMAGE_DIMENSION}). Larger images are scaled down "
            "proportionally; smaller ones pass through unchanged."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the MCP server"""
    args = _build_arg_parser().parse_args(argv)
    set_allowed_directories(args.directories)
    set_max_image_dimension(args.max_image_dimension)
    mcp.run()
