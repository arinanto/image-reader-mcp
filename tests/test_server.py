"""End-to-end tests for the MCP server (in-memory transport)."""
import base64
import io

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from PIL import Image as PILImage

from image_reader_mcp.server import mcp


@pytest.mark.asyncio
async def test_server_exposes_both_tools():
    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.list_tools()
    names = {tool.name for tool in result.tools}
    assert names == {"read_local_image", "read_remote_image"}


@pytest.mark.asyncio
async def test_read_local_image_tool_end_to_end(tmp_path):
    image_path = tmp_path / "sample.png"
    PILImage.new("RGB", (32, 16), (0, 255, 0)).save(image_path, format="PNG")

    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool(
            "read_local_image", {"file_path": str(image_path), "image_size": "16x8"}
        )

    assert not result.isError
    assert result.content, "tool call returned no content"
    image_block = result.content[0]
    assert image_block.type == "image"
    img = PILImage.open(io.BytesIO(base64.b64decode(image_block.data)))
    assert img.size == (16, 8)


@pytest.mark.asyncio
async def test_read_local_image_tool_missing_file(tmp_path):
    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool(
            "read_local_image", {"file_path": str(tmp_path / "does_not_exist.png")}
        )

    # Missing files surface as an error to the MCP client
    assert result.isError
