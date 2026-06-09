"""Headroom context engine plugin for Hermes Agent.

Replaces the built-in ``ContextCompressor``'s LLM-summarization step with
Headroom's deterministic, multi-algorithm compression pipeline. Same
``ContextEngine`` ABC contract — drop-in via ``context.engine: headroom``
in ``~/.hermes/config.yaml``.

Why use it over the built-in compressor?
---------------------------------------
1. **No extra LLM call.** The built-in ``ContextCompressor`` spends a
   second LLM call to *summarize* the middle turns. Headroom's pipeline
   is purely local/deterministic (SmartCrusher + CodeCompressor +
   Kompress-base), so the compression step itself costs zero LLM tokens.
2. **Cache alignment.** Headroom's ``CacheAligner`` stabilizes the prompt
   prefix so Anthropic/OpenAI prompt caches actually hit — turning a
   write-heavy pattern into cache reads. The built-in compressor does not
   do this.
3. **60-95% token reduction** with structured benchmarks (GSM8K ±0.000,
   TruthfulQA +0.030, SQuAD v2 97% accuracy at 19% compression).
4. **Reversible (CCR).** Originals stored locally; agent can call
   ``headroom_retrieve`` to fetch compressed-away chunks on demand.
5. **Cross-agent memory.** Optional shared store across Claude/Codex/
   Hermes with auto-dedup (requires ``headroom-ai[memory]``).

How to enable
-------------
Add to ``~/.hermes/config.yaml``::

    context:
      engine: headroom
      engine_plugins:
        headroom:
          target_ratio: 0.5         # Keep 50% of tokens (aggressive: 0.2, conservative: 0.7)
          protect_recent: 4         # Last N messages always preserved
          kompress_model: null      # null = chopratejas/kompress-base (default)
          compress_user_messages: false   # Skip user messages (coding-agent default)
          compress_system_messages: true
          min_tokens_to_compress: 250
          ccr_enabled: false        # Set true to enable reversible retrieval
          quiet_mode: false

Then ``pip install "headroom-ai[all]"`` and start a session. The engine
gracefully falls back to passthrough if headroom-ai is not installed —
no crash, just no compression (you'll see a warning in the logs).

Backward compatibility
----------------------
The default ``context.engine: compressor`` keeps the existing built-in
behavior. Set ``context.engine: headroom`` to opt in. The plugin never
touches the built-in ``ContextCompressor`` or any other engine.

References
----------
- Headroom docs: https://headroom-docs.vercel.app/docs
- Hermes context engine ABC: ``agent/context_engine.py``
- Plugin discovery: ``plugins/context_engine/__init__.py``
- HermeS CHANGELOG / acceptance: this integration tracked under
  proposal ``P-20260607-001`` in the proposals root.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from agent.context_engine import ContextEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy headroom import — keeps the plugin importable even when headroom-ai
# isn't installed. is_available() exposes the runtime check.
# ---------------------------------------------------------------------------

def _import_headroom():
    """Import headroom's ``compress`` and ``CompressConfig`` lazily.

    Raises ``ImportError`` with an actionable hint if the package is
    missing. Returning a 2-tuple lets callers unpack cleanly::

        compress, CompressConfig = _import_headroom()
    """
    try:
        from headroom import compress, CompressConfig  # type: ignore
        return compress, CompressConfig
    except ImportError as exc:
        raise ImportError(
            "headroom-ai is not installed. "
            "Run: pip install 'headroom-ai[all]'  (or pip install 'headroom-ai' for minimal). "
            f"Original error: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class HeadroomContextEngine(ContextEngine):
    """Context engine that uses Headroom's ``compress()`` for compaction.

    The engine is a drop-in ``ContextEngine`` subclass. Hermes calls the
    same four lifecycle methods it calls on ``ContextCompressor``:

      - ``update_from_response(usage)`` after each LLM turn
      - ``should_compress(prompt_tokens)`` to decide whether to compact
      - ``compress(messages, current_tokens, focus_topic)`` to do the work
      - ``on_session_start/end/reset`` for lifecycle bookkeeping

    It also adds Headroom-specific bookkeeping:

      - ``_total_runs`` / ``_total_tokens_saved`` — session aggregate
      - ``_last_compress_result`` — most recent CompressResult, available
        via ``get_status()`` and via the optional ``headroom_retrieve``
        tool when ``ccr_enabled`` is True.
    """

    # Engine-level compression params (overridable via config.yaml)
    target_ratio: float = 0.5
    protect_recent: int = 4
    kompress_model: Optional[str] = None
    compress_user_messages: bool = False
    compress_system_messages: bool = True
    min_tokens_to_compress: int = 250
    ccr_enabled: bool = False
    quiet_mode: bool = False

    def __init__(
        self,
        model: str = "",
        target_ratio: float = 0.5,
        protect_recent: int = 4,
        kompress_model: Optional[str] = None,
        compress_user_messages: bool = False,
        compress_system_messages: bool = True,
        min_tokens_to_compress: int = 250,
        ccr_enabled: bool = False,
        quiet_mode: bool = False,
    ):
        # Skip the ABC's __init__ — ContextEngine has none, this is just
        # to be explicit and forward-compatible.
        self.target_ratio = target_ratio
        self.protect_recent = protect_recent
        self.kompress_model = kompress_model
        self.compress_user_messages = compress_user_messages
        self.compress_system_messages = compress_system_messages
        self.min_tokens_to_compress = min_tokens_to_compress
        self.ccr_enabled = ccr_enabled
        self.quiet_mode = quiet_mode

        # Session aggregates
        self._total_tokens_saved = 0
        self._total_runs = 0
        self._last_compress_result = None
        self._session_id: Optional[str] = None

        # Model + threshold (set by update_model / on_session_start)
        self.model: str = ""
        self.provider: str = ""
        self.context_length: int = 0
        self.threshold_tokens: int = 0
        if model:
            self._configure_model(model)

    # -- Identity ----------------------------------------------------------

    @property
    def name(self) -> str:
        return "headroom"

    # -- Availability ------------------------------------------------------

    @classmethod
    def is_available(cls) -> bool:
        """Return True if headroom-ai is installed and importable.

        The plugin loader calls this to decide whether to mark the
        engine as available in ``hermes plugins`` / the config wizard.
        The engine itself falls back to passthrough on ImportError
        inside ``compress()`` so a missing package never crashes the
        agent.
        """
        try:
            _import_headroom()
            return True
        except ImportError:
            return False

    # -- Config helpers ----------------------------------------------------

    def _configure_model(self, model: str) -> None:
        """Apply ``model`` + derive context_length / threshold_tokens."""
        self.model = model
        try:
            from agent.model_metadata import get_model_context_length
            self.context_length = int(get_model_context_length(model) or 200000)
        except Exception:
            # Model not in the registry — assume 200K (Anthropic Sonnet 4.5
            # default). Headroom uses this only for the safety ceiling.
            self.context_length = 200000
        self.threshold_tokens = int(self.context_length * self.threshold_percent)

    def apply_config(self, cfg: Dict[str, Any]) -> None:
        """Apply config keys from ``context.engine_plugins.headroom``.

        Unknown keys are ignored. Missing keys keep the constructor
        default. This is invoked by the plugin loader before the
        engine is handed to the agent.
        """
        if not isinstance(cfg, dict):
            return
        for key in (
            "target_ratio", "protect_recent", "kompress_model",
            "compress_user_messages", "compress_system_messages",
            "min_tokens_to_compress", "ccr_enabled", "quiet_mode",
        ):
            if key in cfg:
                setattr(self, key, cfg[key])

    # -- Core ABC: update_from_response ------------------------------------

    def update_from_response(self, usage: Dict[str, Any]) -> None:
        """Update token counters from the latest LLM response.

        Mirrors the base class contract: legacy keys always present,
        canonical buckets optional. We also surface cache_read /
        cache_write tokens because headroom's CacheAligner interacts
        with KV cache hit rates — useful for ``/status`` displays.
        """
        self.last_prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        self.last_completion_tokens = int(usage.get("completion_tokens", 0) or 0)
        self.last_total_tokens = int(usage.get("total_tokens", 0) or 0)
        # Canonical buckets (Anthropic + OpenAI)
        self.last_input_tokens = int(
            usage.get("input_tokens", self.last_prompt_tokens) or 0
        )
        self.last_cache_read_tokens = int(usage.get("cache_read_tokens", 0) or 0)
        self.last_cache_write_tokens = int(usage.get("cache_write_tokens", 0) or 0)
        self.last_reasoning_tokens = int(usage.get("reasoning_tokens", 0) or 0)

    # -- Core ABC: should_compress -----------------------------------------

    def should_compress(self, prompt_tokens: int = None) -> bool:
        """True when ``prompt_tokens`` crosses the threshold."""
        tokens = prompt_tokens if prompt_tokens is not None else self.last_prompt_tokens
        return bool(self.threshold_tokens and tokens and tokens >= self.threshold_tokens)

    # -- Core ABC: compress -------------------------------------------------

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int = None,
        focus_topic: str = None,
    ) -> List[Dict[str, Any]]:
        """Compress ``messages`` via Headroom's pipeline.

        Failure policy: any error (headroom not installed, pipeline
        exception, schema mismatch) falls back to passthrough. Better
        to send uncompacted than to crash the agent loop. The error is
        logged and surfaced via ``get_status()`` for observability.

        ``focus_topic`` is part of the ABC contract but headroom's
        public ``compress()`` does not expose a guided-compression
        knob — we forward it as a kwarg if headroom ever supports it
        (silently ignored today).
        """
        try:
            compress, CompressConfig = _import_headroom()
        except ImportError as exc:
            self._last_error = str(exc)
            if not self.quiet_mode:
                logger.warning("headroom-ai unavailable, passthrough: %s", exc)
            return messages

        if not messages:
            return messages

        cfg = CompressConfig(
            compress_user_messages=self.compress_user_messages,
            compress_system_messages=self.compress_system_messages,
            protect_recent=self.protect_recent,
            target_ratio=self.target_ratio,
            min_tokens_to_compress=self.min_tokens_to_compress,
            kompress_model=self.kompress_model,
        )

        # headroom uses a default model name for token counting. We honor
        # the active model when known, else fall back to a sensible
        # 200K-window default (Anthropic Sonnet 4.5).
        model = self.model or "claude-sonnet-4-5-20250929"

        try:
            result = compress(
                messages,
                model=model,
                model_limit=self.context_length or 200000,
                optimize=True,
                config=cfg,
            )
        except Exception as exc:
            self._last_error = str(exc)
            logger.error("Headroom compression failed, passthrough: %s", exc)
            return messages

        # Bookkeeping
        self._last_error = None
        self._last_compress_result = result
        tokens_saved = int(getattr(result, "tokens_saved", 0) or 0)
        tokens_before = int(getattr(result, "tokens_before", 0) or 0)
        tokens_after = int(getattr(result, "tokens_after", 0) or 0)
        compression_ratio = float(getattr(result, "compression_ratio", 0.0) or 0.0)
        transforms_applied = list(getattr(result, "transforms_applied", []) or [])
        self._total_tokens_saved += tokens_saved
        self._total_runs += 1
        self.compression_count += 1

        if not self.quiet_mode:
            logger.info(
                "Headroom compressed %d → %d tokens "
                "(saved %d, ratio %.2f, transforms=%s)",
                tokens_before,
                tokens_after,
                tokens_saved,
                compression_ratio,
                transforms_applied,
            )

        # CCR: store originals for retrieval (best-effort, no-op if disabled)
        if self.ccr_enabled and getattr(result, "tokens_saved", 0) > 0:
            self._maybe_store_ccr(messages, result)

        return result.messages

    def _maybe_store_ccr(self, originals: List[Dict[str, Any]], result) -> None:
        """Optional: store originals in headroom's CCR for later retrieval.

        Uses the headroom-ai ccr store when available; never raises.
        The ``headroom_retrieve`` tool (see ``get_tool_schemas``) lets the
        agent pull specific originals back if it needs them.
        """
        try:
            from headroom.ccr import store as ccr_store  # type: ignore
        except ImportError:
            return  # CCR not installed; nothing to do
        try:
            session_id = self._session_id or "default"
            ccr_store.put(session_id, result.messages, originals)
        except Exception as exc:
            if not self.quiet_mode:
                logger.debug("CCR store skipped: %s", exc)

    # -- Optional ABC: preflight -------------------------------------------

    def should_compress_preflight(self, messages: List[Dict[str, Any]]) -> bool:
        """Cheap pre-call check: if the rough token estimate already crosses
        the threshold, ask Hermes to pre-compress before the API call.

        We use the same rough estimator the built-in compressor uses for
        parity. headroom's pipeline itself is fast (sub-second for typical
        conversations), so preflighting is mostly about avoiding an API
        call that we *know* will fail.
        """
        try:
            from agent.model_metadata import estimate_messages_tokens_rough
            rough = estimate_messages_tokens_rough(messages)
        except Exception:
            return False
        return bool(self.threshold_tokens and rough >= self.threshold_tokens)

    # -- Optional ABC: lifecycle -------------------------------------------

    def on_session_start(self, session_id: str, **kwargs) -> None:
        """Reset per-session aggregates and capture session id.

        Hermes may pass ``model=``, ``provider=``, ``hermes_home=`` etc.
        via kwargs — we honor ``model`` and ``provider``.
        """
        self._session_id = session_id
        self._total_tokens_saved = 0
        self._total_runs = 0
        self._last_compress_result = None
        self._last_error = None
        if kwargs.get("model"):
            self._configure_model(kwargs["model"])
        if kwargs.get("provider"):
            self.provider = kwargs["provider"]

    def on_session_end(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Log the session's final headroom stats (info-level)."""
        if not self.quiet_mode and self._total_runs:
            logger.info(
                "Headroom session %s: %d compression run(s), "
                "%d total tokens saved, last error=%s",
                session_id, self._total_runs, self._total_tokens_saved,
                self._last_error or "none",
            )

    def on_session_reset(self) -> None:
        """Reset for /new or /reset."""
        super().on_session_reset()
        self._total_tokens_saved = 0
        self._total_runs = 0
        self._last_compress_result = None
        self._last_error = None

    # -- Optional ABC: model switch ----------------------------------------

    def update_model(
        self,
        model: str,
        context_length: int,
        base_url: str = "",
        api_key: str = "",
        provider: str = "",
        api_mode: str = "",
    ) -> None:
        """Hermes calls this when the user switches models or on fallback.

        We re-derive ``context_length`` from the model registry when
        available (and trust the caller's value otherwise), then
        recompute the threshold. Provider is captured because headroom's
        content router uses provider-specific token counting hints.
        """
        if model:
            self._configure_model(model)
        else:
            # No model change — just update threshold
            self.context_length = int(context_length or self.context_length or 200000)
            self.threshold_tokens = int(self.context_length * self.threshold_percent)
        if provider:
            self.provider = provider

    # -- Optional ABC: status ----------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Return the standard status dict plus headroom-specific fields.

        Hermes' ``/status`` command and the CLI banner both read this.
        """
        s = super().get_status()
        s.update({
            "engine": "headroom",
            "headroom_available": self.is_available(),
            "headroom_runs": self._total_runs,
            "headroom_total_tokens_saved": self._total_tokens_saved,
            "headroom_target_ratio": self.target_ratio,
            "headroom_protect_recent": self.protect_recent,
            "headroom_ccr_enabled": self.ccr_enabled,
            "headroom_model": self.model,
            "headroom_last_error": getattr(self, "_last_error", None),
        })
        return s

    # -- Optional ABC: tools -----------------------------------------------

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Expose ``headroom_retrieve`` to the agent when CCR is enabled.

        The LLM can call this to pull a specific original message that
        was compressed away. With CCR off, retrieval is meaningless
        (originals aren't stored), so we don't advertise the tool.
        """
        if not self.ccr_enabled or not self.is_available():
            return []
        return [{
            "type": "function",
            "function": {
                "name": "headroom_retrieve",
                "description": (
                    "Retrieve an original message that was compressed away "
                    "by the headroom context engine. Use the index from the "
                    "most recent compression summary to pull a specific turn."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "index": {
                            "type": "integer",
                            "description": (
                                "Index of the original message in the "
                                "pre-compression transcript (0-based)"
                            ),
                        }
                    },
                    "required": ["index"],
                },
            },
        }]

    def handle_tool_call(self, name: str, args: Dict[str, Any], **kwargs) -> str:
        """Handle the ``headroom_retrieve`` tool call. Always returns JSON."""
        if name != "headroom_retrieve":
            return super().handle_tool_call(name, args, **kwargs)
        try:
            from headroom.ccr import store as ccr_store  # type: ignore
        except ImportError:
            return json.dumps({"ok": False, "error": "headroom-ai CCR not installed"})
        try:
            session_id = self._session_id or "default"
            msg = ccr_store.get(session_id, int(args.get("index", -1)))
            return json.dumps({"ok": True, "message": msg})
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)})

    # -- Optional: has_content_to_compress ---------------------------------

    def has_content_to_compress(self, messages: List[Dict[str, Any]]) -> bool:
        """Preflight for manual ``/compress``.

        Cheaper than running the full pipeline. Returns True if any
        message is large enough to be a compression candidate.
        """
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str) and len(content) > 1000:
                return True
            if isinstance(content, list):
                # Multi-part content (Anthropic format)
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text", "")
                        if isinstance(text, str) and len(text) > 1000:
                            return True
        return False


# ---------------------------------------------------------------------------
# Plugin registration (standard ``register(ctx)`` pattern).
#
# The plugin loader in ``plugins/context_engine/__init__.py`` first tries
# the ``register(ctx)`` hook, then falls back to discovering a top-level
# ``ContextEngine`` subclass. We provide both so the engine is
# discoverable even if the loader's preference order changes.
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register this engine with the plugin loader's collector.

    ``ctx`` is a ``_EngineCollector`` (see
    ``plugins/context_engine/__init__.py``) that records the engine
    instance for the loader to return. We instantiate with no args —
    the engine's config gets pushed in via ``update_model()`` once
    the active session is known.
    """
    ctx.register_context_engine(HeadroomContextEngine())


__all__ = ["HeadroomContextEngine", "register"]
