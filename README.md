# Image Reader MCP

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that
lets LLMs read images from local file paths and remote URLs. Images are returned
as PNG content blocks ready for analysis.

> **Version 1.0.0-rc1** — this release **removes** the per-call `image_size`
> parameter. See [Breaking changes in 1.0.0](#breaking-changes-in-100).

## Key Features

- **Local image support** — read images from local filesystem paths
- **Remote image support** — fetch images over HTTP(S)
- **Automatic downscaling** — images larger than a configurable maximum dimension are scaled down proportionally; smaller images pass through unchanged
- **Multiple formats** — JPEG, PNG, GIF, BMP, and anything else Pillow can decode
- **Strict path allowlist** — local reads are restricted to the directories given on the command line; everything else is rejected
- **Self-contained binaries** — tagged releases ship a single PyInstaller executable per platform, no Python install required
- **Robust errors** — clear failures for non-HTTP URLs, non-image responses, missing files, and invalid configuration

## Breaking changes in 1.0.0

`1.0.0` removes the per-call `image_size` parameter from both read tools. Image
resolution is now a **server setting** instead of a per-call argument, so every
request is scaled the same way.

| 0.2.x | 1.0.0 |
| --- | --- |
| `read_local_image(file_path, image_size="128x128")` | `read_local_image(file_path)` |
| `read_remote_image(url, timeout=30, image_size="128x128")` | `read_remote_image(url, timeout=30)` |
| Free-form `"WIDTHxHEIGHT"` resize (could upscale or distort) | `--max-image-dimension N` — longest side capped, aspect ratio preserved, never upscaled |

**Migration:** drop the `image_size` argument from your calls and, if you relied
on a resolution other than the new default, start the server with the flag:

```json
"args": ["--max-image-dimension", "1024", "/path/to/images"]
```

Also new in `1.0.0`: the [`list_allowed_directories`](#list_allowed_directories) tool.

## Requirements

- VS Code, Cursor, Windsurf, Claude Desktop, or any other MCP client

The prebuilt binaries are self-contained, so no Python installation is required.

## Installation

Every tagged release ships a single self-contained executable for Linux, macOS
(Apple silicon), and Windows on the
[releases page](https://github.com/arinanto/image-reader-mcp/releases).

```bash
# Example: Linux x86_64
chmod +x image-reader-mcp-linux-x86_64
./image-reader-mcp-linux-x86_64 /path/to/images
```

### Allowed directories

Directories listed after the executable are the only places `read_local_image`
may read from. Pass several to allow multiple directories:

```bash
./image-reader-mcp-linux-x86_64 /dir1 /dir2 /dir3
```

If no directories are given, **all local reads are denied** (remote reads still
work). Use the `list_allowed_directories` tool to see what the server allows.

### Maximum image dimension

Images are returned at their original resolution unless their longest side
exceeds the maximum image dimension, which defaults to **1600** pixels. Override
it with `--max-image-dimension`:

```bash
./image-reader-mcp-linux-x86_64 --max-image-dimension 1024 /path/to/images
```

The aspect ratio is always preserved, and images already within the limit are
returned untouched — they are never upscaled.

> **macOS:** the binaries are unsigned, so Gatekeeper may quarantine them after
download. Clear the flag with `xattr -d com.apple.quarantine <binary>`.

## Configuration

Point your MCP client at the downloaded executable, passing the allowlisted
directories (and optionally the maximum dimension) as arguments:

```json
{
  "mcpServers": {
    "image-reader": {
      "command": "/path/to/image-reader-mcp",
      "args": ["--max-image-dimension", "1600", "/path/to/images"]
    }
  }
}
```

## Tools

### `read_local_image`

Read an image from a local file path.

- `file_path` (required): absolute path to the image; must be inside one of the
  directories the server was started with.

### `read_remote_image`

Fetch an image from a remote URL.

- `url` (required): URL of the remote image (HTTP or HTTPS).
- `timeout` (optional): request timeout in seconds (default: `30`).

### `list_allowed_directories`

List the directories the server allows local images to be read from, as resolved
absolute paths. Takes no arguments. Returns an empty list when the server was
started without any directory, meaning all local reads are denied.

Both image tools return the image at its original resolution unless its longest
side exceeds `--max-image-dimension` (default `1600`), in which case it is scaled
down proportionally.

## Usage Examples

```python
# Local image
read_local_image("/path/to/image.jpg")

# Remote image
read_remote_image("https://example.com/image.jpg")

# Remote image with a custom timeout
read_remote_image("https://example.com/image.png", timeout=60)

# Inspect the allowlist
list_allowed_directories()
```

## Development

### Local installation

```bash
git clone https://github.com/arinanto/image-reader-mcp.git
cd image-reader-mcp
uv sync
```

### Running the server

```bash
uv run python -m image_reader_mcp /dir1 /dir2
```

### Building a standalone binary

The [PyInstaller](https://pyinstaller.org/) spec at the repository root bundles
the server and its dependencies into one executable:

```bash
uv run pyinstaller image-reader-mcp.spec --clean --noconfirm
```

The result is `dist/image-reader-mcp` (`dist/image-reader-mcp.exe` on Windows).
The `Build binaries` workflow builds the Linux, macOS, and Windows binaries on
tagged releases and attaches them to the GitHub release.

### Running tests

```bash
uv run pytest
```

## License

Released under the [MIT License](LICENSE).
