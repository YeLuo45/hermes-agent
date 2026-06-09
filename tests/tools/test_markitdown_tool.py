"""Tests for the markitdown tool.

``convert_to_markdown`` wraps Microsoft's markitdown library so agents
can read PDF/Word/Excel/PPT/Image/Audio/HTML/ZIP/EPUB/YouTube when
``read_file`` blocks them as binary.

Tests mock markitdown at the import boundary so the suite runs without
the (heavy) library installed. Coverage:

  - Schema + registration
  - Availability check (markitdown missing vs present)
  - Lazy install path (calls ``tools.lazy_deps.ensure``)
  - Local path: happy path, file size cap, missing file, oversized file
  - URL: happy path, blocked by website policy
  - Truncation at ``max_chars``
  - Format detection
  - Error paths: import failure, conversion failure, no path
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# markitdown mocking helper
# ---------------------------------------------------------------------------

class _FakeConversionResult:
    """Stand-in for markitdown's DocumentConverterResult."""
    def __init__(self, markdown_text):
        self.markdown = markdown_text


class _FakeMarkItDown:
    """Stand-in for markitdown.MarkItDown.

    Class-level ``_next_markdown`` is the canned return value for the
    next ``convert()`` call (tests set it before each call).
    """
    _next_markdown = "# default\n"
    last_source = None
    last_instance = None

    def __init__(self, *args, **kwargs):
        _FakeMarkItDown.last_instance = self

    def convert(self, source, **kwargs):
        _FakeMarkItDown.last_source = source
        return _FakeConversionResult(_FakeMarkItDown._next_markdown)


def _set_next(markdown_text):
    """Set the canned return value for the next markitdown.convert() call."""
    _FakeMarkItDown._next_markdown = markdown_text


def _install_fake_markitdown(monkeypatch, *, available=True, conversion_error=None):
    """Install or remove a fake ``markitdown`` module for one test."""
    if not available:
        for mod_name in list(sys.modules):
            if mod_name == "markitdown" or mod_name.startswith("markitdown."):
                monkeypatch.delitem(sys.modules, mod_name, raising=False)
        import tools.markitdown_tool as mdt
        monkeypatch.setattr(mdt, "_check_markitdown_available", lambda: False)
        monkeypatch.setattr(mdt, "_try_lazy_install", lambda: None)
        return None

    fake = sys.modules.get("markitdown")
    if fake is None or fake.__class__.__name__ != "module":
        fake = type(sys)("markitdown")
    _FakeMarkItDown._next_markdown = "# default\n"
    _FakeMarkItDown.last_source = None
    _FakeMarkItDown.last_instance = None

    if conversion_error is None:
        fake.MarkItDown = _FakeMarkItDown  # type: ignore[attr-defined]
    else:
        class _RaisingMarkItDown:
            def convert(self, *a, **k):
                raise conversion_error
        fake.MarkItDown = _RaisingMarkItDown  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "markitdown", fake)
    # Restore real probe + lazy installer in our tool
    import tools.markitdown_tool as mdt
    monkeypatch.setattr(
        mdt, "_check_markitdown_available",
        lambda: "markitdown" in sys.modules,
    )
    monkeypatch.setattr(mdt, "_try_lazy_install", lambda: None)
    return fake


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_markitdown(monkeypatch):
    """markitdown is importable and converts happily to '# default\\n'."""
    return _install_fake_markitdown(monkeypatch, available=True)


@pytest.fixture()
def fake_markitdown_missing(monkeypatch):
    """markitdown is not importable; lazy install will be tried."""
    return _install_fake_markitdown(monkeypatch, available=False)


@pytest.fixture(autouse=True)
def _reset_caches():
    """Reset the in-test state of the fake between tests."""
    _FakeMarkItDown._next_markdown = "# default\n"
    _FakeMarkItDown.last_source = None
    _FakeMarkItDown.last_instance = None


# ---------------------------------------------------------------------------
# Schema + registration
# ---------------------------------------------------------------------------

class TestSchema:
    def test_schema_has_required_path(self):
        from tools.markitdown_tool import CONVERT_TO_MARKDOWN_SCHEMA
        assert CONVERT_TO_MARKDOWN_SCHEMA["name"] == "convert_to_markdown"
        assert "path" in CONVERT_TO_MARKDOWN_SCHEMA["parameters"]["required"]

    def test_schema_optional_max_chars(self):
        from tools.markitdown_tool import CONVERT_TO_MARKDOWN_SCHEMA
        props = CONVERT_TO_MARKDOWN_SCHEMA["parameters"]["properties"]
        assert "max_chars" in props
        assert props["max_chars"]["default"] == 50_000

    def test_schema_optional_max_input_bytes(self):
        from tools.markitdown_tool import CONVERT_TO_MARKDOWN_SCHEMA
        props = CONVERT_TO_MARKDOWN_SCHEMA["parameters"]["properties"]
        assert "max_input_bytes" in props
        assert props["max_input_bytes"]["default"] == 200 * 1024 * 1024

    def test_registered_with_registry(self):
        from tools.registry import registry
        from tools.markitdown_tool import CONVERT_TO_MARKDOWN_SCHEMA
        entry = registry.get_entry("convert_to_markdown")
        assert entry is not None
        assert entry.toolset == "file"
        assert entry.schema == CONVERT_TO_MARKDOWN_SCHEMA


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_check_returns_true_when_fake_installed(self, fake_markitdown):
        from tools.markitdown_tool import _check_markitdown_available
        assert _check_markitdown_available() is True

    def test_check_returns_false_when_missing(self, fake_markitdown_missing):
        from tools.markitdown_tool import _check_markitdown_available
        assert _check_markitdown_available() is False


# ---------------------------------------------------------------------------
# Local path: happy path
# ---------------------------------------------------------------------------

class TestLocalPath:
    def test_convert_local_pdf(self, fake_markitdown):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4 fake content")
            tmp_path = tmp.name
        try:
            _set_next("# Extracted PDF Content\n\nLorem ipsum.")
            result = json.loads(_call_tool({"path": tmp_path}))
            assert "error" not in result
            assert result["success"] is True
            assert "Extracted PDF Content" in result["content"]
            assert result["metadata"]["format"] == "pdf"
            assert result["metadata"]["file_bytes"] > 0
            assert result["metadata"]["truncated"] is False
        finally:
            os.unlink(tmp_path)

    def test_convert_passes_resolved_path(self, fake_markitdown):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            _call_tool({"path": tmp_path})
            assert _FakeMarkItDown.last_source is not None
            assert os.path.isabs(_FakeMarkItDown.last_source)
        finally:
            os.unlink(tmp_path)

    def test_path_with_tilde_expanded(self, fake_markitdown):
        # Tilde expansion happens, then we hit "file not found"
        result = json.loads(_call_tool({"path": "~/nonexistent_xyzzy.pdf"}))
        assert "error" in result
        assert "File not found" in result["error"]

    def test_relative_path_resolved(self, fake_markitdown):
        rel = "_test_markitdown_relative.docx"
        with open(rel, "w") as f:
            f.write("dummy")
        try:
            _set_next("# OK")
            result = json.loads(_call_tool({"path": rel}))
            assert "error" not in result
            assert _FakeMarkItDown.last_source and os.path.isabs(_FakeMarkItDown.last_source)
        finally:
            os.unlink(rel)

    def test_missing_file(self, fake_markitdown):
        result = json.loads(_call_tool({"path": "/nonexistent/path/file.pdf"}))
        assert "error" in result
        assert "File not found" in result["error"]

    def test_directory_not_a_file(self, fake_markitdown):
        with tempfile.TemporaryDirectory() as d:
            result = json.loads(_call_tool({"path": d}))
            assert "error" in result
            assert "Not a regular file" in result["error"]


# ---------------------------------------------------------------------------
# File size guard
# ---------------------------------------------------------------------------

class TestFileSizeGuard:
    def test_oversized_file_refused(self, fake_markitdown):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"small")
            tmp_path = tmp.name
        try:
            real_stat = os.stat(tmp_path)

            class _FakeStat:
                st_size = 500 * 1024 * 1024  # 500 MB
                st_mode = real_stat.st_mode

            with patch("pathlib.Path.stat", return_value=_FakeStat()):
                result = json.loads(_call_tool({
                    "path": tmp_path,
                    "max_input_bytes": 100 * 1024 * 1024,
                }))
                assert "error" in result
                assert "too large" in result["error"].lower()
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

class TestTruncation:
    def test_truncates_long_output(self, fake_markitdown):
        big = "# Big\n\n" + ("lorem ipsum " * 5000)  # ~60K chars
        _set_next(big)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = json.loads(_call_tool({"path": tmp_path, "max_chars": 1000}))
            assert "error" not in result
            assert result["metadata"]["truncated"] is True
            assert result["metadata"]["original_chars"] > 1000
            assert result["metadata"]["returned_chars"] <= 1100
            assert "[...truncated" in result["content"]
        finally:
            os.unlink(tmp_path)

    def test_no_truncation_when_fits(self, fake_markitdown):
        _set_next("# Short\n\nHi")
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = json.loads(_call_tool({"path": tmp_path, "max_chars": 50_000}))
            assert result["metadata"]["truncated"] is False
            assert result["content"] == "# Short\n\nHi"
        finally:
            os.unlink(tmp_path)

    def test_min_max_chars_enforced(self, fake_markitdown):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = json.loads(_call_tool({"path": tmp_path, "max_chars": 100}))
            assert "error" in result
            assert "max_chars" in result["error"]
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# URL handling
# ---------------------------------------------------------------------------

class TestURLs:
    def test_youtube_url(self, fake_markitdown, monkeypatch):
        _set_next("# YouTube Transcript\n\nSpeaker said hi.")
        monkeypatch.setattr(
            "tools.website_policy.check_website_access",
            lambda url: True,
            raising=False,
        )
        result = json.loads(_call_tool({"path": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}))
        assert "error" not in result
        assert result["metadata"]["format"] == "url:www.youtube.com"
        assert "YouTube Transcript" in result["content"]
        assert _FakeMarkItDown.last_source == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_https_url(self, fake_markitdown, monkeypatch):
        _set_next("# Page\n\n...")
        monkeypatch.setattr(
            "tools.website_policy.check_website_access",
            lambda url: True,
            raising=False,
        )
        result = json.loads(_call_tool({"path": "https://example.com/doc.html"}))
        assert "error" not in result
        assert result["metadata"]["format"] == "url:example.com"

    def test_url_blocked_by_policy(self, fake_markitdown, monkeypatch):
        monkeypatch.setattr(
            "tools.website_policy.check_website_access",
            lambda url: False,
            raising=False,
        )
        result = json.loads(_call_tool({"path": "https://blocked.example.com/"}))
        assert "error" in result
        assert "Blocked by website policy" in result["error"]

    def test_ftp_url_routes_to_local_path(self, fake_markitdown):
        # ftp:// not in the allow-list → falls through to local-path branch
        result = json.loads(_call_tool({"path": "ftp://example.com/file"}))
        assert "error" in result


# ---------------------------------------------------------------------------
# Lazy install
# ---------------------------------------------------------------------------

class TestLazyInstall:
    def test_lazy_install_called_when_missing(self, monkeypatch):
        import tools.markitdown_tool as mdt
        state = {"installed": False, "ensure_calls": 0}

        def fake_check():
            return state["installed"]

        def fake_ensure():
            state["ensure_calls"] += 1
            state["installed"] = True
            fake_mod = type(sys)("markitdown")
            fake_mod.MarkItDown = _FakeMarkItDown  # type: ignore[attr-defined]
            sys.modules["markitdown"] = fake_mod
            _set_next("# installed!")

        monkeypatch.setattr(mdt, "_check_markitdown_available", fake_check)
        monkeypatch.setattr(mdt, "_try_lazy_install", fake_ensure)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = json.loads(_call_tool({"path": tmp_path}))
            assert "error" not in result
            assert "installed!" in result["content"]
            assert state["ensure_calls"] == 1
        finally:
            os.unlink(tmp_path)

    def test_lazy_install_failure_returns_error(self, monkeypatch):
        import tools.markitdown_tool as mdt

        def fake_check():
            return False

        def fake_ensure_fail():
            raise RuntimeError("pip install failed: offline")

        monkeypatch.setattr(mdt, "_check_markitdown_available", fake_check)
        monkeypatch.setattr(mdt, "_try_lazy_install", fake_ensure_fail)

        result = json.loads(_call_tool({"path": "anything.txt"}))
        assert "error" in result
        assert "markitdown is not installed" in result["error"]
        assert "offline" in result["error"]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

class TestErrors:
    def test_no_path_arg(self, fake_markitdown):
        result = json.loads(_call_tool({}))
        assert "error" in result
        assert "path" in result["error"].lower()

    def test_empty_path(self, fake_markitdown):
        result = json.loads(_call_tool({"path": "   "}))
        assert "error" in result

    def test_conversion_failure(self, monkeypatch):
        _install_fake_markitdown(
            monkeypatch, available=True, conversion_error=RuntimeError("corrupt file")
        )
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"corrupt")
            tmp_path = tmp.name
        try:
            result = json.loads(_call_tool({"path": tmp_path}))
            assert "error" in result
            assert "conversion failed" in result["error"]
            assert "corrupt file" in result["error"]
        finally:
            os.unlink(tmp_path)

    def test_empty_markdown_result(self, fake_markitdown):
        # Markitdown might return empty string for unparseable inputs
        _set_next("")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"junk")
            tmp_path = tmp.name
        try:
            result = json.loads(_call_tool({"path": tmp_path}))
            assert "error" not in result
            assert result["content"] == ""
            assert result["metadata"]["original_chars"] == 0
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Helper: invocation via the registered tool
# ---------------------------------------------------------------------------

def _call_tool(args):
    """Invoke the registered convert_to_markdown handler directly."""
    from tools.markitdown_tool import _handle_convert_to_markdown
    return _handle_convert_to_markdown(args, task_id="test")


# ---------------------------------------------------------------------------
# Helper coverage
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_is_url_recognizes_http(self):
        from tools.markitdown_tool import _is_url
        assert _is_url("http://example.com/x") is True
        assert _is_url("https://example.com/x") is True
        assert _is_url("file:///tmp/x.pdf") is True
        assert _is_url("data:text/plain,hi") is True

    def test_is_url_rejects_local(self):
        from tools.markitdown_tool import _is_url
        assert _is_url("/tmp/file.pdf") is False
        assert _is_url("./relative.docx") is False
        assert _is_url("file.pdf") is False
        assert _is_url("ftp://example.com") is False  # not in allow-list

    def test_truncate_short_passthrough(self):
        from tools.markitdown_tool import _truncate
        assert _truncate("hello", 100) == "hello"

    def test_truncate_long_breaks_on_newline(self):
        from tools.markitdown_tool import _truncate
        text = "x" * 800 + "\n\n" + "y" * 800  # newline at position 800
        truncated = _truncate(text, 1000)
        assert "[...truncated" in truncated
        # The 'y' section should NOT be present (cut at the newline)
        assert "yyy" not in truncated

    def test_truncate_no_newline_near_end(self):
        from tools.markitdown_tool import _truncate
        text = "x" * 2000  # no newline
        truncated = _truncate(text, 1000)
        assert "[...truncated" in truncated
        assert len(truncated) < 1100

    def test_detect_format(self):
        from tools.markitdown_tool import _detect_format
        assert _detect_format("/tmp/foo.PDF") == "pdf"
        assert _detect_format("bar.docx") == "docx"
        assert _detect_format("noext") == "unknown"
