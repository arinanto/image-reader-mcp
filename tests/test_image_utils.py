"""Tests for image_reader_mcp.image_utils"""
import io

import pytest
from PIL import Image as PILImage

from image_reader_mcp import image_utils


def _png_bytes(result: image_utils.Image) -> bytes:
    """Return the raw PNG bytes carried by a FastMCP ``Image`` result.

    ``Image.data`` is typed ``bytes | None`` (the class also accepts a ``path``),
    so narrow it here once instead of at every call site.
    """
    data = result.data
    assert data is not None, "expected inline image data, got a path-based Image"
    return data


class TestPathAllowlist:
    def test_allows_file_inside_directory(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        image = allowed / "pic.png"
        image.write_bytes(b"x")
        assert image_utils.is_path_allowed(str(image), [str(allowed)])

    def test_allows_the_directory_itself(self, tmp_path):
        assert image_utils.is_path_allowed(str(tmp_path), [str(tmp_path)])

    def test_rejects_file_outside_all_directories(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside.png"
        outside.write_bytes(b"x")
        assert not image_utils.is_path_allowed(str(outside), [str(allowed)])

    def test_rejects_sibling_with_same_prefix(self, tmp_path):
        allowed = tmp_path / "dir1"
        sibling = tmp_path / "dir10"
        allowed.mkdir()
        sibling.mkdir()
        image = sibling / "pic.png"
        image.write_bytes(b"x")
        # /dir10 must not be treated as inside /dir1
        assert not image_utils.is_path_allowed(str(image), [str(allowed)])

    def test_rejects_parent_traversal(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        (tmp_path / "secret.png").write_bytes(b"x")
        traversal = allowed / ".." / "secret.png"
        assert not image_utils.is_path_allowed(str(traversal), [str(allowed)])

    def test_rejects_symlink_escape(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside.png"
        outside.write_bytes(b"x")
        link = allowed / "link.png"
        link.symlink_to(outside)
        # The symlink lives inside the allowed dir but resolves outside it.
        assert not image_utils.is_path_allowed(str(link), [str(allowed)])

    def test_allows_any_of_multiple_directories(self, tmp_path):
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        image = second / "pic.png"
        image.write_bytes(b"x")
        assert image_utils.is_path_allowed(str(image), [str(first), str(second)])

    def test_empty_allowlist_denies_everything(self, tmp_path):
        image = tmp_path / "pic.png"
        image.write_bytes(b"x")
        assert not image_utils.is_path_allowed(str(image), [])

    def test_assert_raises_with_allowed_directories_in_message(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside.png"
        outside.write_bytes(b"x")
        with pytest.raises(PermissionError) as excinfo:
            image_utils.assert_path_allowed(str(outside), [str(allowed)])
        message = str(excinfo.value)
        assert "forbidden" in message
        assert str(allowed) in message

    def test_assert_mentions_none_when_allowlist_empty(self, tmp_path):
        image = tmp_path / "pic.png"
        image.write_bytes(b"x")
        with pytest.raises(PermissionError) as excinfo:
            image_utils.assert_path_allowed(str(image), [])
        assert "(none configured)" in str(excinfo.value)

    def test_assert_passes_for_allowed_path(self, tmp_path):
        image = tmp_path / "pic.png"
        image.write_bytes(b"x")
        image_utils.assert_path_allowed(str(image), [str(tmp_path)])


@pytest.fixture
def sample_image(tmp_path) -> str:
    """Create a small real PNG on disk and return its path."""
    path = tmp_path / "sample.png"
    PILImage.new("RGB", (32, 16), (255, 0, 0)).save(path, format="PNG")
    return str(path)


@pytest.fixture
def large_image(tmp_path) -> str:
    """Create a large landscape PNG (3200x1600) and return its path."""
    path = tmp_path / "large.png"
    PILImage.new("RGB", (3200, 1600), (0, 0, 255)).save(path, format="PNG")
    return str(path)


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, content: bytes, content_type: str | None = None, status_code: int = 200):
        self.content = content
        self.headers = {"Content-Type": content_type} if content_type else {}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class TestMaxDimensionValidation:
    @pytest.mark.parametrize("value", [1, 16, 1600])
    def test_accepts_positive_integers(self, value):
        assert image_utils._validate_max_dimension(value) == value

    @pytest.mark.parametrize("value", [0, -1, -1600])
    def test_rejects_non_positive(self, value):
        with pytest.raises(ValueError):
            image_utils._validate_max_dimension(value)

    @pytest.mark.parametrize("value", [1.5, "1600", None, True])
    def test_rejects_non_int(self, value):
        with pytest.raises(ValueError):
            image_utils._validate_max_dimension(value)


class TestLoadLocalImage:
    def test_returns_png(self, sample_image):
        result = image_utils.load_local_image(sample_image, 1600)
        data = _png_bytes(result)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes
        img = PILImage.open(io.BytesIO(data))
        assert img.format == "PNG"

    def test_small_image_passes_through_unchanged(self, sample_image):
        # The 32x16 sample is below the cap, so it must not be touched.
        result = image_utils.load_local_image(sample_image, 64)
        img = PILImage.open(io.BytesIO(_png_bytes(result)))
        assert img.size == (32, 16)

    def test_landscape_longest_side_is_capped(self, large_image):
        result = image_utils.load_local_image(large_image, 1600)
        img = PILImage.open(io.BytesIO(_png_bytes(result)))
        assert img.size == (1600, 800)

    def test_portrait_longest_side_is_capped(self, tmp_path):
        path = tmp_path / "portrait.png"
        PILImage.new("RGB", (1600, 3200), (0, 255, 0)).save(path, format="PNG")
        result = image_utils.load_local_image(str(path), 1600)
        img = PILImage.open(io.BytesIO(_png_bytes(result)))
        assert img.size == (800, 1600)

    def test_image_exactly_at_cap_is_unchanged(self, tmp_path):
        path = tmp_path / "exact.png"
        PILImage.new("RGB", (1600, 800), (0, 0, 0)).save(path, format="PNG")
        result = image_utils.load_local_image(str(path), 1600)
        img = PILImage.open(io.BytesIO(_png_bytes(result)))
        assert img.size == (1600, 800)

    def test_default_dimension_is_1600(self, large_image):
        # 3200x1600 with no explicit dimension must cap at the default 1600.
        result = image_utils.load_local_image(large_image)
        img = PILImage.open(io.BytesIO(_png_bytes(result)))
        assert img.size == (1600, 800)

    @pytest.mark.parametrize("max_dimension", [0, -10])
    def test_invalid_max_dimension_raises(self, sample_image, max_dimension):
        with pytest.raises(ValueError):
            image_utils.load_local_image(sample_image, max_dimension)

    def test_non_image_file_raises(self, tmp_path):
        path = tmp_path / "not_image.txt"
        path.write_text("definitely not an image")
        with pytest.raises(PILImage.UnidentifiedImageError):
            image_utils.load_local_image(str(path))


class TestLoadRemoteImage:
    def _read_sample_png(self, sample_image: str) -> bytes:
        with open(sample_image, "rb") as f:
            return f.read()

    def test_landscape_longest_side_is_capped(self, monkeypatch, sample_image):
        png = self._read_sample_png(sample_image)
        monkeypatch.setattr(
            image_utils.requests, "get",
            lambda url, timeout=None: FakeResponse(png, "image/png"),
        )
        result = image_utils.load_remote_image("https://example.com/img.png", max_dimension=16)
        data = _png_bytes(result)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes
        img = PILImage.open(io.BytesIO(data))
        assert img.size == (16, 8)

    def test_small_image_passes_through_unchanged(self, monkeypatch, sample_image):
        png = self._read_sample_png(sample_image)
        monkeypatch.setattr(
            image_utils.requests, "get",
            lambda url, timeout=None: FakeResponse(png, "image/png"),
        )
        result = image_utils.load_remote_image("https://example.com/img.png", max_dimension=1600)
        img = PILImage.open(io.BytesIO(_png_bytes(result)))
        assert img.size == (32, 16)

    def test_accepts_content_type_with_parameters(self, monkeypatch, sample_image):
        png = self._read_sample_png(sample_image)
        monkeypatch.setattr(
            image_utils.requests, "get",
            lambda url, timeout=None: FakeResponse(png, "image/jpeg; charset=binary"),
        )
        # "image/jpeg; charset=binary" must not trip the content-type check
        image_utils.load_remote_image("https://example.com/img.jpg")

    def test_rejects_non_image_content_type(self, monkeypatch):
        monkeypatch.setattr(
            image_utils.requests, "get",
            lambda url, timeout=None: FakeResponse(b"<html>oops</html>", "text/html"),
        )
        with pytest.raises(ValueError, match="Content-Type"):
            image_utils.load_remote_image("https://example.com/page")

    def test_missing_content_type_falls_back_to_pil(self, monkeypatch, sample_image):
        png = self._read_sample_png(sample_image)
        monkeypatch.setattr(
            image_utils.requests, "get",
            lambda url, timeout=None: FakeResponse(png),
        )
        result = image_utils.load_remote_image("https://example.com/img.png")
        img = PILImage.open(io.BytesIO(_png_bytes(result)))
        assert img.size == (32, 16)

    def test_invalid_max_dimension_raises_before_network(self, monkeypatch):
        def _boom(url, timeout=None):
            raise AssertionError("network should not be touched")
        monkeypatch.setattr(image_utils.requests, "get", _boom)
        with pytest.raises(ValueError):
            image_utils.load_remote_image("https://example.com/img.png", max_dimension=0)

    def test_invalid_timeout_raises(self, monkeypatch):
        def _boom(url, timeout=None):
            raise AssertionError("network should not be touched")
        monkeypatch.setattr(image_utils.requests, "get", _boom)
        with pytest.raises(ValueError):
            image_utils.load_remote_image("https://example.com/img.png", timeout=0)

    @pytest.mark.parametrize(
        "url",
        ["ftp://example.com/img.png", "file:///etc/passwd", "not a url", "javascript:alert(1)"],
    )
    def test_rejects_non_http_schemes(self, monkeypatch, url):
        def _boom(url, timeout=None):
            raise AssertionError("network should not be touched")
        monkeypatch.setattr(image_utils.requests, "get", _boom)
        with pytest.raises(ValueError, match="http or https"):
            image_utils.load_remote_image(url)
