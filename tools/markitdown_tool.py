"""Markitdown tool — convert files/URLs to Markdown for LLM consumption.

Microsoft's `markitdown` (14.6k stars, MIT) turns a wide range of formats
into clean, LLM-friendly Markdown:

  * PDF (.pdf) — text + structure
  * PowerPoint (.pptx)
  * Word (.docx)
  * Excel (.xlsx, .xls)
  * Images (.png, .jpg, ...) — EXIF + OCR
  * Audio (.mp3, .wav, ...) — EXIF + speech transcription
  * HTML (.html, .htm)
  * Text-based (.csv, .json, .xml)
  * ZIP — iterates over contents
  * EPUB
  * YouTube URLs — fetches the transcript
  * + more via plugins

Why this matters in Hermes
--------------------------
``read_file`` **blocks** binary formats by extension (PDF, DOCX, PPTX,
XLSX, ...) for safety — agents currently have no way to read those
files. This tool fills that gap for the formats markitdown understands,
opt-in via the existing ``lazy_deps`` allowlist.

Enabling
--------
Markitdown is **not** installed by default. The first call to
``convert_to_markdown`` triggers a one-shot install into the active venv
(via ``tools.lazy_deps.ensure("convert.markitdown")``), assuming
``security.allow_lazy_installs`` is ``True`` (the default).

To pre-install manually::

    pip install 'markitdown[all]'

Then it's available without any lazy install at runtime.

Backward compatibility
----------------------
* Existing ``read_file`` behavior is unchanged. PDFs are still blocked
  from ``read_file``; this tool is the explicit way to convert them.
* If markitdown is not installed AND lazy installs are disabled, the
  tool returns a structured error pointing at the manual install
  command. The agent's call fails gracefully — no crash.

References
----------
* markitdown: https://github.com/microsoft/markitdown
* Hermes tool registry: ``tools/registry.py``
* Lazy install: ``tools/lazy_deps.py``
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

# Default cap on returned markdown characters. The model's context is the
# real bottleneck — 50K chars ≈ 12-18K tokens, safe for most 200K-window
# models. Override per-call via the ``max_chars`` parameter.
_DEFAULT_MAX_CHARS = 50_000

# Hard upper bound on input file size. Refuses to even open anything
# larger to avoid OOM on, e.g., a 2GB PDF. Configurable per-call via
# ``max_input_bytes``.
_DEFAULT_MAX_INPUT_BYTES = 200 * 1024 * 1024  # 200 MB

# Allow URLs we know markitdown handles well (YouTube transcripts, plus
# the local / file / http(s) schemes we explicitly trust). Anything else
# gets routed to the standard web_extract tool instead.
_URL_SCHEMES_ALLOWED = frozenset({"http", "https", "file", "data"})


# ---------------------------------------------------------------------------
# Availability check (fast — no imports executed)
# ---------------------------------------------------------------------------

def _check_markitdown_available() -> bool:
    """Return True when ``markitdown`` is importable.

    Uses :func:`importlib.util.find_spec` to probe without executing
    ``__init__`` — see the comment in :mod:`tools.feishu_doc_tool` for
    why we don't just ``import markitdown`` here.
    """
    try:
        return importlib.util.find_spec("markitdown") is not None
    except (ImportError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Lazy-install helper
# ---------------------------------------------------------------------------

def _try_lazy_install() -> None:
    """Attempt a one-shot venv-scoped install of markitdown.

    No-op if already importable, if the user has disabled lazy installs,
    or if the install fails (caller catches + reports).
    """
    try:
        from tools.lazy_deps import ensure, FeatureUnavailable
        ensure("convert.markitdown")
    except ImportError:
        # lazy_deps module missing — should never happen in a real install
        return
    except Exception as exc:  # noqa: BLE001 — surface install hint to caller
        # ``ensure`` raises FeatureUnavailable with a remediation hint;
        # we let the caller turn that into a tool_error.
        raise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_url(s: str) -> bool:
    """True when ``s`` looks like a URL (scheme + netloc OR file/data).

    file:// and data: URIs may have an empty netloc (they address
    local resources), so we don't require netloc for those schemes.
    For http/https we DO require a netloc — bare "http://" or
    "https://foo" with no path/host is malformed.
    """
    try:
        parsed = urlparse(s)
    except Exception:
        return False
    if parsed.scheme not in _URL_SCHEMES_ALLOWED:
        return False
    # file: and data: may have no netloc
    if parsed.scheme in ("file", "data"):
        return True
    return bool(parsed.netloc)


def _is_local_path(s: str) -> bool:
    """True when ``s`` looks like a local file path (exists or not).

    Excludes URLs — the caller has already routed those elsewhere.
    """
    if _is_url(s):
        return False
    return bool(s) and not s.isspace()


def _truncate(text: str, max_chars: int) -> str:
    """Truncate ``text`` to ``max_chars`` characters.

    Tries to break on a newline boundary so the agent doesn't see a
    half-sentence at the cut. Returns the original if it already fits.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_nl = truncated.rfind("\n")
    if last_nl > max_chars * 0.8:  # only break on newline if near the end
        truncated = truncated[:last_nl]
    return truncated + "\n\n[...truncated — output exceeded max_chars limit]"


def _detect_format(path: str) -> str:
    """Best-effort format description for metadata."""
    ext = Path(path).suffix.lower()
    return ext.lstrip(".") or "unknown"


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

CONVERT_TO_MARKDOWN_SCHEMA = {
    "name": "convert_to_markdown",
    "description": (
        "Convert a local file (PDF, Word, PowerPoint, Excel, image, audio, "
        "HTML, CSV/JSON/XML, ZIP, EPUB, ...) or a supported URL (YouTube, "
        "http/https, file://, data:) to clean Markdown text. "
        "Useful when an LLM needs to read a binary document that ``read_file`` "
        "blocks for safety. Powered by Microsoft's markitdown library. "
        "Returns the markdown text plus a metadata block (format, size, "
        "truncation status)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Local file path (absolute or relative to cwd) OR a "
                    "URL (http/https/file/data, including YouTube URLs for "
                    "transcript extraction). One of ``path`` is required."
                ),
            },
            "max_chars": {
                "type": "integer",
                "description": (
                    "Maximum characters to return (default 50000). The output "
                    "is truncated to this size with a marker; pick a smaller "
                    "value when the model has limited context."
                ),
                "default": _DEFAULT_MAX_CHARS,
                "minimum": 1000,
                "maximum": 500_000,
            },
            "max_input_bytes": {
                "type": "integer",
                "description": (
                    "Refuse to open input files larger than this many bytes "
                    "(default 200 MB). Prevents OOM on accidentally-large PDFs."
                ),
                "default": _DEFAULT_MAX_INPUT_BYTES,
                "minimum": 1024,
            },
        },
        "required": ["path"],
    },
}


def _handle_convert_to_markdown(args: Dict[str, Any], **kwargs: Any) -> str:
    """The handler registered with the tool registry.

    Failure policy: every error path returns a JSON tool_error with an
    actionable remediation hint. The agent's call never crashes.
    """
    path = (args.get("path") or "").strip()
    if not path:
        return tool_error("'path' is required (local file path or URL)")

    max_chars = int(args.get("max_chars") or _DEFAULT_MAX_CHARS)
    max_input_bytes = int(args.get("max_input_bytes") or _DEFAULT_MAX_INPUT_BYTES)
    if max_chars < 1000:
        return tool_error("max_chars must be at least 1000")

    # ── Lazy install (no-op if already importable) ─────────────────────
    if not _check_markitdown_available():
        try:
            _try_lazy_install()
        except Exception as exc:
            return tool_error(
                "markitdown is not installed and lazy install failed. "
                "Install manually with: pip install 'markitdown[all]'. "
                f"Underlying error: {exc}"
            )
        # Re-probe after install
        if not _check_markitdown_available():
            return tool_error(
                "markitdown is not importable after lazy install. "
                "Install manually with: pip install 'markitdown[all]'."
            )

    # ── Real import (we know it's available now) ──────────────────────
    try:
        from markitdown import MarkItDown  # type: ignore
    except ImportError as exc:
        return tool_error(f"markitdown import failed: {exc}")

    # ── Local-path size guard ─────────────────────────────────────────
    is_url = _is_url(path)
    if not is_url:
        if not _is_local_path(path):
            return tool_error(
                f"Invalid 'path': not a URL and not a local file path: {path!r}"
            )
        try:
            resolved = Path(path).expanduser().resolve()
        except Exception as exc:
            return tool_error(f"Could not resolve path {path!r}: {exc}")
        if not resolved.exists():
            return tool_error(f"File not found: {path}")
        if not resolved.is_file():
            return tool_error(f"Not a regular file: {path}")
        try:
            size = resolved.stat().st_size
        except OSError as exc:
            return tool_error(f"Could not stat {path!r}: {exc}")
        if size > max_input_bytes:
            return tool_error(
                f"File too large: {size} bytes (limit {max_input_bytes}). "
                "Use max_input_bytes to override, or pre-process the file."
            )
        # Honor the website blocklist for file:// URIs
        if str(resolved).startswith("file://"):
            try:
                from tools.website_policy import check_website_access
                if not check_website_access(str(resolved)):
                    return tool_error(f"Blocked by website policy: {path}")
            except Exception:
                pass
        source_for_md = str(resolved)
        fmt = _detect_format(source_for_md)
    else:
        # URL: apply website blocklist via the same hook
        try:
            from tools.website_policy import check_website_access
            if not check_website_access(path):
                return tool_error(f"Blocked by website policy: {path}")
        except Exception:
            pass
        source_for_md = path
        fmt = "url:" + urlparse(path).netloc

    # ── Convert ──────────────────────────────────────────────────────
    try:
        converter = MarkItDown()
        result = converter.convert(source_for_md)
    except Exception as exc:
        logger.warning("markitdown.convert failed for %s: %s", path, exc)
        return tool_error(f"markitdown conversion failed: {exc}")

    markdown = getattr(result, "markdown", None) or ""
    original_len = len(markdown)
    was_truncated = original_len > max_chars
    if was_truncated:
        markdown = _truncate(markdown, max_chars)

    # Build metadata block
    metadata: Dict[str, Any] = {
        "format": fmt,
        "source": path,
        "original_chars": original_len,
        "returned_chars": len(markdown),
        "truncated": was_truncated,
    }
    if not is_url:
        try:
            metadata["file_bytes"] = resolved.stat().st_size  # type: ignore[name-defined]
        except Exception:
            pass

    logger.info(
        "markitdown.convert %s: %d → %d chars (truncated=%s)",
        path, original_len, len(markdown), was_truncated,
    )
    return tool_result(success=True, content=markdown, metadata=metadata)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="convert_to_markdown",
    toolset="file",
    schema=CONVERT_TO_MARKDOWN_SCHEMA,
    handler=_handle_convert_to_markdown,
    check_fn=_check_markitdown_available,
    requires_env=[],
    is_async=False,
    description=(
        "Convert PDF/Word/Excel/PPT/Image/Audio/HTML/ZIP/EPUB/YouTube to Markdown "
        "(via Microsoft markitdown). Fills the gap left by read_file's binary block."
    ),
    emoji="📄",
    # Mark as a per-result large-output tool: the handler itself enforces
    # a per-call ``max_chars`` cap (default 50K), but allow a generous
    # absolute ceiling for callers that explicitly raise the cap.
    max_result_size_chars=500_000,
)
