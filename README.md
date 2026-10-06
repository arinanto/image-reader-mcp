# Image Reader MCP

A Model Context Protocol (MCP) server for reading and processing local and remote images. This server enables LLMs to load, resize, and analyze images from file paths or URLs.

## Key Features

- **Local image support**: Read images from local file system paths
- **Remote image support**: Fetch and process images from URLs  
- **Automatic resizing**: Configurable image resizing for optimal processing
- **Multiple formats**: Support for common image formats (JPEG, PNG, GIF, BMP, etc.)
- **Input validation**: Clear errors for malformed `image_size` strings, non-HTTP URLs, and non-image responses
- **Strict path allowlist**: Local reads are restricted to directories given on the command line; anything else is rejected
- **Self-contained binaries**: Tagged releases ship a single PyInstaller executable per platform — no Python install required
- **Error handling**: Robust error handling for missing files and network issues

## Requirements

- VS Code, Cursor, Windsurf, Claude Desktop, or any other MCP client

The prebuilt binaries are self-contained, so no Python installation is required.

## Installation

Every tagged release (`v*`) ships a single self-contained executable for Linux,
macOS (Intel and Apple silicon), and Windows on the
[releases page](https://github.com/arinanto/image-reader-mcp/releases).

```bash
# Example: Linux x86_64
chmod +x image-reader-mcp-linux-x86_64
./image-reader-mcp-linux-x86_64 /path/to/images
```

Directories listed after the executable are the only places `read_local_image` is
allowed to read from. Pass several to allow multiple directories:

```bash
./image-reader-mcp-linux-x86_64 /dir1 /dir2 /dir3
```

If no directories are given, **all local reads are denied** (remote reads still work).

> **macOS:** the binaries are unsigned, so Gatekeeper may quarantine them after
download. Clear the flag with `xattr -d com.apple.quarantine <binary>`.

## Configuration

Point your MCP client at the downloaded executable, passing the allowed
directories as arguments:

```json
{
  "mcpServers": {
    "image-reader": {
      "command": "/path/to/image-reader-mcp",
      "args": ["/path/to/images"]
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
git clone https://github.com/arinanto/image-reader-mcp.git
cd image-reader-mcp
uv sync
```

### Running the Server

```bash
uv run python -m image_reader_mcp /dir1 /dir2
```

### Building a Standalone Binary

The [PyInstaller](https://pyinstaller.org/) spec at the repository root bundles
the server and its dependencies into one executable:

```bash
uv run pyinstaller image-reader-mcp.spec --clean --noconfirm
```

The result is `dist/image-reader-mcp` (`dist/image-reader-mcp.exe` on Windows).
The `Build binaries` GitHub Actions workflow builds all four platform binaries on
tagged releases and attaches them to the GitHub release.

### Running Tests

```bash
uv run pytest
```

## License

This project is licensed under the MIT License.
