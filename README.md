# Image Reader MCP

A Model Context Protocol (MCP) server for reading and processing local and remote images. This server enables LLMs to load, resize, and analyze images from file paths or URLs.

## Key Features

- **Local image support**: Read images from local file system paths
- **Remote image support**: Fetch and process images from URLs  
- **Automatic resizing**: Configurable image resizing for optimal processing
- **Multiple formats**: Support for common image formats (JPEG, PNG, GIF, BMP, etc.)
- **Input validation**: Clear errors for malformed `image_size` strings, non-HTTP URLs, and non-image responses
- **Strict path allowlist**: Local reads are restricted to directories given on the command line; anything else is rejected
- **Error handling**: Robust error handling for missing files and network issues

## Requirements

- Python 3.12 or newer
- VS Code, Cursor, Windsurf, Claude Desktop, or any other MCP client

## Installation

```bash
uvx --from git+https://github.com/k2sebeom/image-reader-mcp@main image-reader-mcp /path/to/images
```

Any directories listed after `image-reader-mcp` are the only places `read_local_image`
is allowed to read from. Pass several to allow multiple directories:

```bash
uvx --from git+https://github.com/k2sebeom/image-reader-mcp@main image-reader-mcp /dir1 /dir2 /dir3
```

If no directories are given, **all local reads are denied** (remote reads still work).

## Configuration

Add the server to your MCP client configuration, passing the allowed directories as
arguments:

```json
{
  "mcpServers": {
    "image-reader": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/k2sebeom/image-reader-mcp@main",
        "image-reader-mcp",
        "/path/to/images"
      ]
    }
  }
}
```

## Tools

### Image Processing

- **read_local_image**: Read and process images from local file paths
  - `file_path` (required): Absolute path to the local image file; must be inside one of the directories the server was started with
  - `image_size` (optional): Resize format as "WIDTHxHEIGHT" (default: "128x128")

- **read_remote_image**: Fetch and process images from remote URLs
  - `url` (required): URL of the remote image
  - `timeout` (optional): Request timeout in seconds (default: 30)
  - `image_size` (optional): Resize format as "WIDTHxHEIGHT" (default: "128x128")

## Usage Examples

### Reading Local Images

```python
# Read a local image with default size
read_local_image("/path/to/image.jpg")

# Read a local image with custom size
read_local_image("/path/to/image.png", "256x256")
```

### Reading Remote Images

```python
# Fetch an image from URL
read_remote_image("https://example.com/image.jpg")

# Fetch with custom timeout and size
read_remote_image("https://example.com/image.png", timeout=60, image_size="512x512")
```

## Development

### Local Installation

```bash
git clone https://github.com/k2sebeom/image-reader-mcp.git
cd image-reader-mcp
uv sync
```

### Running the Server

```bash
uv run image-reader-mcp /dir1 /dir2
```

### Running Tests

```bash
uv run pytest
```

## License

This project is licensed under the MIT License.
