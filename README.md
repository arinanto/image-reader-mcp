# Image Reader MCP

A Model Context Protocol (MCP) server for reading and processing local and remote images. This server enables LLMs to load, resize, and analyze images from file paths or URLs.

## Key Features

- **Local image support**: Read images from local file system paths
- **Remote image support**: Fetch and process images from URLs  
- **Automatic resizing**: Configurable image resizing for optimal processing
- **Multiple formats**: Support for common image formats (JPEG, PNG, GIF, BMP, etc.)
- **Error handling**: Robust error handling for missing files and network issues

## Requirements

- Python 3.12 or newer
- VS Code, Cursor, Windsurf, Claude Desktop, or any other MCP client

## Installation

```bash
uvx --from https://github.com/k2sebeom/image-reader-mcp@main image-reader-mcp
```

## Configuration

Add the server to your MCP client configuration:

```json
{
  "mcpServers": {
    "image-reader": {
      "command": "uvx",
      "args": ["--from", "https://github.com/k2sebeom/image-reader-mcp@main", "image-reader-mcp"]
    }
  }
}
```

## Tools

### Image Processing

- **read_local_image**: Read and process images from local file paths
  - `file_path` (required): Absolute path to the local image file
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

### Running Tests

```bash
uv run pytest
```

## License

This project is licensed under the MIT License.
