"""End-to-end tests for the MCP server (in-memory transport)."""
import base64
import io

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from PIL import Image as PILImage

import image_reader_mcp.server as server
from image_reader_mcp import image_utils
from image_reader_mcp.server import main, mcp


@pytest.fixture(autouse=True)
def _reset_server_config():
    """Keep the module-level allowlist and max dimension from leaking between tests."""
    server.set_allowed_directories([])
    server.set_max_image_dimension(image_utils.DEFAULT_MAX_IMAGE_DIMENSION)
    yield
    server.set_allowed_directories([])
    server.set_max_image_dimension(image_utils.DEFAULT_MAX_IMAGE_DIMENSION)


def _text(result) -> str:
    return "\n".join(block.text for block in result.content if block.type == "text")


@pytest.mark.asyncio
async def test_server_exposes_all_tools():
    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.list_tools()
    names = {tool.name for tool in result.tools}
    assert names == {"read_local_image", "read_remote_image", "list_allowed_directories"}


@pytest.mark.asyncio
async def test_list_allowed_directories_tool_returns_configured_dirs(tmp_path):
    first = tmp_path / "first"
    first.mkdir()
    server.set_allowed_directories([str(first)])

    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool("list_allowed_directories", {})

    assert not result.isError
    assert str(first.resolve()) in _text(result)


@pytest.mark.asyncio
async def test_list_allowed_directories_tool_empty_when_unconfigured():
    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool("list_allowed_directories", {})

    assert not result.isError
    assert _text(result).strip() in {"[]", ""}


@pytest.mark.asyncio
async def test_read_local_image_tool_end_to_end(tmp_path):
    image_path = tmp_path / "sample.png"
    PILImage.new("RGB", (32, 16), (0, 255, 0)).save(image_path, format="PNG")
    server.set_allowed_directories([str(tmp_path)])
    server.set_max_image_dimension(16)

    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool("read_local_image", {"file_path": str(image_path)})

    assert not result.isError
    assert result.content, "tool call returned no content"
    image_block = result.content[0]
    assert image_block.type == "image"
    img = PILImage.open(io.BytesIO(base64.b64decode(image_block.data)))
    assert img.size == (16, 8)


@pytest.mark.asyncio
async def test_read_local_image_tool_missing_file(tmp_path):
    server.set_allowed_directories([str(tmp_path)])

    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool(
            "read_local_image", {"file_path": str(tmp_path / "does_not_exist.png")}
        )

    # Missing files surface as an error to the MCP client
    assert result.isError


@pytest.mark.asyncio
async def test_read_local_image_tool_rejects_path_outside_allowed(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.png"
    PILImage.new("RGB", (4, 4), (0, 0, 255)).save(outside, format="PNG")
    server.set_allowed_directories([str(allowed)])

    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool("read_local_image", {"file_path": str(outside)})

    assert result.isError
    message = _text(result)
    assert "forbidden" in message
    assert str(allowed) in message


@pytest.mark.asyncio
async def test_read_local_image_tool_denies_all_when_unconfigured(tmp_path):
    image_path = tmp_path / "sample.png"
    PILImage.new("RGB", (4, 4), (0, 255, 0)).save(image_path, format="PNG")

    async with create_connected_server_and_client_session(mcp) as session:
        await session.initialize()
        result = await session.call_tool("read_local_image", {"file_path": str(image_path)})

    assert result.isError
    assert "none configured" in _text(result)


class TestCliArguments:
    def test_no_arguments_yields_empty_allowlist(self):
        args = server._build_arg_parser().parse_args([])
        assert args.directories == []

    def test_multiple_directories(self):
        args = server._build_arg_parser().parse_args(["/dir1", "/dir2", "/dir3"])
        assert args.directories == ["/dir1", "/dir2", "/dir3"]

    def test_max_image_dimension_defaults_to_1600(self):
        args = server._build_arg_parser().parse_args([])
        assert args.max_image_dimension == 1600

    def test_max_image_dimension_override(self):
        args = server._build_arg_parser().parse_args(["--max-image-dimension", "512"])
        assert args.max_image_dimension == 512

    @pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5"])
    def test_invalid_max_image_dimension_rejected(self, value):
        with pytest.raises(SystemExit):
            server._build_arg_parser().parse_args(["--max-image-dimension", value])

    def test_set_allowed_directories_resolves_paths(self, tmp_path):
        server.set_allowed_directories([str(tmp_path)])
        assert server.list_allowed_directories() == [str(tmp_path.resolve())]

    def test_main_registers_directories_before_run(self, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(server.mcp, "run", lambda: calls.append("run"))
        main([str(tmp_path)])
        assert calls == ["run"]
        assert server.list_allowed_directories() == [str(tmp_path.resolve())]

    def test_main_sets_max_image_dimension(self, monkeypatch):
        monkeypatch.setattr(server.mcp, "run", lambda: None)
        main(["--max-image-dimension", "256"])
        assert server._max_image_dimension == 256
