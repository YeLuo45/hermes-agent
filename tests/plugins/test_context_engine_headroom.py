"""Tests for the headroom context engine plugin.

The headroom engine is a ContextEngine subclass that wraps
``headroom.compress()`` for deterministic message compression. These
tests mock the headroom-ai package at the import boundary so the test
suite runs without requiring headroom-ai to be installed.

Coverage:
  - Plugin discovery (the loader finds the engine)
  - is_available() — True when headroom-ai is importable, False otherwise
  - apply_config() — config_keys push in correctly
  - should_compress() — threshold logic
  - update_from_response() — usage dict → instance state
  - compress() — happy path with mocked headroom, plus the
                 "headroom-ai not installed" passthrough fallback
  - compress() error passthrough — pipeline exception never crashes
  - get_status() — engine-specific fields present
  - get_tool_schemas() / handle_tool_call() — CCR retrieval tool
  - on_session_start/end/reset — lifecycle bookkeeping
"""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Headroom import mocking helpers
# ---------------------------------------------------------------------------

def _install_fake_headroom(monkeypatch, *, available: bool = True, side_effect=None):
    """Install or remove a fake ``headroom`` module for one test.

    ``available=False`` simulates the "headroom-ai not installed" case
    by removing the module from sys.modules. ``available=True`` installs
    a stub with the ``compress`` function and ``CompressConfig`` class
    that can be further customized.

    Returns the fake module so tests can configure it.
    """
    if not available:
        # Make sure the import raises ImportError
        for mod_name in list(sys.modules):
            if mod_name == "headroom" or mod_name.startswith("headroom."):
                monkeypatch.delitem(sys.modules, mod_name, raising=False)
        # Patch _import_headroom to raise
        import plugins.context_engine.headroom as hr_mod
        monkeypatch.setattr(hr_mod, "_import_headroom",
                            MagicMock(side_effect=ImportError("headroom-ai not installed (test)")))
        return None

    # Build a fake headroom package. ModuleType + setattr is too strict
    # for pyright; we use a plain class and inject it as "headroom".
    fake_compress = MagicMock(side_effect=side_effect)
    fake_compress.return_value = _make_result_mock()  # default happy return

    class FakeCompressConfig:
        """Mimics headroom.CompressConfig — a dataclass accepting kwargs."""
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _FakeHeadroom:
        compress = fake_compress
        CompressConfig = FakeCompressConfig

    fake = _FakeHeadroom()
    monkeypatch.setitem(sys.modules, "headroom", fake)
    # Also reset the module's cached import inside our plugin
    import plugins.context_engine.headroom as hr_mod
    def fake_import():
        return fake_compress, FakeCompressConfig
    monkeypatch.setattr(hr_mod, "_import_headroom", fake_import)
    return fake


def _make_result_mock(tokens_before=1000, tokens_after=500, tokens_saved=500,
                      compression_ratio=0.5, transforms=None):
    """Build a CompressResult-like mock."""
    r = MagicMock()
    r.messages = [{"role": "user", "content": "compressed"}]
    r.tokens_before = tokens_before
    r.tokens_after = tokens_after
    r.tokens_saved = tokens_saved
    r.compression_ratio = compression_ratio
    r.transforms_applied = transforms or ["SmartCrusher", "CacheAligner"]
    return r


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_headroom(monkeypatch):
    """Headroom-ai is importable; default return is a plausible CompressResult."""
    fake = _install_fake_headroom(monkeypatch, available=True)
    fake.compress.return_value = _make_result_mock()
    return fake


@pytest.fixture()
def headroom_engine(fake_headroom):
    """A HeadroomContextEngine with model pre-configured for tests."""
    from plugins.context_engine.headroom import HeadroomContextEngine
    with patch("agent.model_metadata.get_model_context_length", return_value=200000):
        eng = HeadroomContextEngine(model="claude-sonnet-4-5-20250929", quiet_mode=True)
    return eng


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

class TestDiscovery:
    """The plugin loader must find the headroom engine."""

    def test_engine_dir_exists(self):
        from pathlib import Path
        engine_dir = Path(__file__).resolve().parents[2] / "plugins" / "context_engine" / "headroom"
        assert engine_dir.is_dir(), f"headroom engine dir missing: {engine_dir}"
        assert (engine_dir / "__init__.py").is_file()
        assert (engine_dir / "plugin.yaml").is_file()

    def test_discover_context_engines_finds_headroom(self, fake_headroom):
        from plugins.context_engine import discover_context_engines
        engines = discover_context_engines()
        names = [n for n, _desc, _avail in engines]
        assert "headroom" in names, f"headroom not discovered; got: {names}"

    def test_discover_includes_description_from_yaml(self, fake_headroom):
        from plugins.context_engine import discover_context_engines
        engines = discover_context_engines()
        hr_entry = next(((n, d, a) for n, d, a in engines if n == "headroom"), None)
        assert hr_entry is not None
        name, desc, available = hr_entry
        # Description pulled from plugin.yaml
        assert "60-95%" in desc or "deterministic" in desc.lower()

    def test_load_context_engine_returns_instance(self, fake_headroom):
        from plugins.context_engine import load_context_engine
        engine = load_context_engine("headroom")
        assert engine is not None
        assert engine.name == "headroom"
        assert hasattr(engine, "compress")
        assert hasattr(engine, "should_compress")

    def test_load_unknown_engine_returns_none(self, fake_headroom):
        from plugins.context_engine import load_context_engine
        assert load_context_engine("does-not-exist-xyz") is None

    def test_register_pattern_works(self, fake_headroom):
        """The plugin's register(ctx) pattern should populate the collector."""
        from plugins.context_engine.headroom import register
        from plugins.context_engine import _EngineCollector
        collector = _EngineCollector(engine_name="headroom")
        register(collector)
        assert collector.engine is not None
        assert collector.engine.name == "headroom"


# ---------------------------------------------------------------------------
# Identity + availability
# ---------------------------------------------------------------------------

class TestIdentity:
    def test_name_is_headroom(self, headroom_engine):
        assert headroom_engine.name == "headroom"

    def test_is_available_when_headroom_present(self, headroom_engine):
        assert headroom_engine.is_available() is True

    def test_is_available_false_when_headroom_missing(self, monkeypatch):
        _install_fake_headroom(monkeypatch, available=False)
        from plugins.context_engine.headroom import HeadroomContextEngine
        eng = HeadroomContextEngine(quiet_mode=True)
        assert eng.is_available() is False

    def test_is_classmethod_works(self, fake_headroom):
        from plugins.context_engine.headroom import HeadroomContextEngine
        # is_available must be callable on the class too (loader uses it)
        assert HeadroomContextEngine.is_available() is True


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class TestApplyConfig:
    def test_apply_config_overrides_known_keys(self, headroom_engine):
        headroom_engine.apply_config({
            "target_ratio": 0.3,
            "protect_recent": 8,
            "ccr_enabled": True,
            "quiet_mode": True,
        })
        assert headroom_engine.target_ratio == 0.3
        assert headroom_engine.protect_recent == 8
        assert headroom_engine.ccr_enabled is True
        assert headroom_engine.quiet_mode is True

    def test_apply_config_ignores_unknown_keys(self, headroom_engine):
        original = headroom_engine.target_ratio
        headroom_engine.apply_config({
            "target_ratio": 0.7,
            "totally_unknown_key": "ignored",
        })
        assert headroom_engine.target_ratio == 0.7
        assert not hasattr(headroom_engine, "totally_unknown_key")

    def test_apply_config_handles_non_dict(self, headroom_engine):
        # No-op
        headroom_engine.apply_config("not a dict")
        headroom_engine.apply_config(None)
        # Nothing should have blown up
        assert headroom_engine.target_ratio == 0.5


# ---------------------------------------------------------------------------
# Token tracking
# ---------------------------------------------------------------------------

class TestUpdateFromResponse:
    def test_updates_legacy_fields(self, headroom_engine):
        headroom_engine.update_from_response({
            "prompt_tokens": 1234,
            "completion_tokens": 56,
            "total_tokens": 1290,
        })
        assert headroom_engine.last_prompt_tokens == 1234
        assert headroom_engine.last_completion_tokens == 56
        assert headroom_engine.last_total_tokens == 1290

    def test_updates_canonical_buckets(self, headroom_engine):
        headroom_engine.update_from_response({
            "prompt_tokens": 1000,
            "completion_tokens": 50,
            "input_tokens": 900,
            "output_tokens": 50,
            "cache_read_tokens": 800,
            "cache_write_tokens": 100,
            "reasoning_tokens": 10,
        })
        assert headroom_engine.last_input_tokens == 900
        assert headroom_engine.last_cache_read_tokens == 800
        assert headroom_engine.last_cache_write_tokens == 100
        assert headroom_engine.last_reasoning_tokens == 10

    def test_handles_missing_keys(self, headroom_engine):
        headroom_engine.update_from_response({})
        assert headroom_engine.last_prompt_tokens == 0
        assert headroom_engine.last_total_tokens == 0


class TestShouldCompress:
    def test_below_threshold_no_compress(self, headroom_engine):
        # 200000 * 0.75 = 150000 threshold
        headroom_engine.last_prompt_tokens = 100_000
        assert headroom_engine.should_compress() is False

    def test_at_threshold_compresses(self, headroom_engine):
        headroom_engine.last_prompt_tokens = 150_000
        assert headroom_engine.should_compress() is True

    def test_above_threshold_compresses(self, headroom_engine):
        headroom_engine.last_prompt_tokens = 200_000
        assert headroom_engine.should_compress() is True

    def test_explicit_prompt_tokens(self, headroom_engine):
        assert headroom_engine.should_compress(prompt_tokens=200_000) is True
        assert headroom_engine.should_compress(prompt_tokens=10_000) is False

    def test_zero_threshold_never_compresses(self, fake_headroom):
        from plugins.context_engine.headroom import HeadroomContextEngine
        with patch("agent.model_metadata.get_model_context_length", return_value=0):
            eng = HeadroomContextEngine(model="x", quiet_mode=True)
        eng.threshold_tokens = 0
        eng.last_prompt_tokens = 999_999
        assert eng.should_compress() is False


# ---------------------------------------------------------------------------
# Compression
# ---------------------------------------------------------------------------

class TestCompress:
    def test_compress_happy_path(self, headroom_engine, fake_headroom):
        messages = [
            {"role": "system", "content": "you are a helpful assistant"},
            {"role": "user", "content": "hello" * 200},  # big-ish
            {"role": "assistant", "content": "hi"},
        ]
        result = headroom_engine.compress(messages, current_tokens=5000)
        # Returns the (mocked) compressed messages
        assert result == [{"role": "user", "content": "compressed"}]
        # headroom.compress was called with our config
        assert fake_headroom.compress.call_count == 1
        call_kwargs = fake_headroom.compress.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"
        assert call_kwargs["optimize"] is True
        assert call_kwargs["config"] is not None
        # Bookkeeping updated
        assert headroom_engine._total_runs == 1
        assert headroom_engine._total_tokens_saved == 500
        assert headroom_engine.compression_count == 1

    def test_compress_passes_protect_recent(self, headroom_engine, fake_headroom):
        headroom_engine.protect_recent = 7
        headroom_engine.compress([{"role": "user", "content": "x"}])
        # The CompressConfig instance gets the right protect_recent value
        cfg_kwarg = fake_headroom.compress.call_args.kwargs["config"]
        assert cfg_kwarg.kwargs["protect_recent"] == 7

    def test_compress_empty_messages_returns_empty(self, headroom_engine, fake_headroom):
        assert headroom_engine.compress([]) == []
        # headroom.compress not called for empty input
        fake_headroom.compress.assert_not_called()

    def test_compress_passthrough_when_headroom_missing(self, monkeypatch):
        _install_fake_headroom(monkeypatch, available=False)
        from plugins.context_engine.headroom import HeadroomContextEngine
        eng = HeadroomContextEngine(model="x", quiet_mode=True)
        messages = [{"role": "user", "content": "hello"}]
        result = eng.compress(messages)
        # Passthrough — no compression
        assert result == messages
        assert eng._last_error and "headroom-ai" in eng._last_error.lower()

    def test_compress_passthrough_on_pipeline_error(self, headroom_engine, fake_headroom):
        fake_headroom.compress.side_effect = RuntimeError("pipeline blew up")
        messages = [{"role": "user", "content": "test"}]
        result = headroom_engine.compress(messages)
        # Passthrough on error — never crash the agent loop
        assert result == messages
        assert "pipeline blew up" in (headroom_engine._last_error or "")

    def test_compress_logs_transforms(self, headroom_engine, fake_headroom, caplog):
        import logging
        caplog.set_level(logging.INFO, logger="plugins.context_engine.headroom")
        # Un-quiet for this test so the log fires
        headroom_engine.quiet_mode = False
        fake_headroom.compress.return_value = _make_result_mock(
            transforms=["SmartCrusher", "Kompress-base", "CacheAligner"]
        )
        headroom_engine.compress([{"role": "user", "content": "x" * 5000}])
        # The "Headroom compressed ..." line should mention all 3 transforms
        text = "\n".join(r.message for r in caplog.records)
        assert "SmartCrusher" in text
        assert "CacheAligner" in text

    def test_compress_aggregates_across_runs(self, headroom_engine, fake_headroom):
        fake_headroom.compress.return_value = _make_result_mock(tokens_saved=300)
        headroom_engine.compress([{"role": "user", "content": "a"}])
        headroom_engine.compress([{"role": "user", "content": "b"}])
        assert headroom_engine._total_runs == 2
        assert headroom_engine._total_tokens_saved == 600


# ---------------------------------------------------------------------------
# CCR (Compress-Compress-Retrieve) — optional retrieval tool
# ---------------------------------------------------------------------------

class TestCCR:
    def test_tool_schemas_empty_when_ccr_disabled(self, headroom_engine):
        # ccr_enabled defaults to False
        assert headroom_engine.get_tool_schemas() == []

    def test_tool_schemas_empty_when_headroom_missing(self, monkeypatch):
        _install_fake_headroom(monkeypatch, available=False)
        from plugins.context_engine.headroom import HeadroomContextEngine
        eng = HeadroomContextEngine(model="x", ccr_enabled=True, quiet_mode=True)
        assert eng.get_tool_schemas() == []

    def test_tool_schemas_present_when_ccr_enabled(self, headroom_engine):
        headroom_engine.ccr_enabled = True
        schemas = headroom_engine.get_tool_schemas()
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "headroom_retrieve"
        assert "index" in schema["function"]["parameters"]["properties"]

    def test_handle_unknown_tool(self, headroom_engine):
        out = headroom_engine.handle_tool_call("nope", {})
        parsed = json.loads(out)
        assert "error" in parsed
        assert "Unknown context engine tool" in parsed["error"]


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class TestGetStatus:
    def test_status_includes_engine_name(self, headroom_engine):
        s = headroom_engine.get_status()
        assert s["engine"] == "headroom"
        assert s["headroom_available"] is True

    def test_status_includes_aggregates(self, headroom_engine, fake_headroom):
        headroom_engine.compress([{"role": "user", "content": "x" * 5000}])
        s = headroom_engine.get_status()
        assert s["headroom_runs"] == 1
        assert s["headroom_total_tokens_saved"] == 500
        assert s["headroom_target_ratio"] == 0.5
        assert s["headroom_protect_recent"] == 4

    def test_status_includes_last_error(self, headroom_engine, fake_headroom):
        fake_headroom.compress.side_effect = RuntimeError("nope")
        headroom_engine.compress([{"role": "user", "content": "x"}])
        s = headroom_engine.get_status()
        assert "nope" in s["headroom_last_error"]


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_on_session_start_resets_aggregates(self, headroom_engine, fake_headroom):
        headroom_engine.compress([{"role": "user", "content": "x"}])
        assert headroom_engine._total_runs == 1
        headroom_engine.on_session_start(session_id="sess-42", model="claude-opus-4-20250514")
        assert headroom_engine._total_runs == 0
        assert headroom_engine._total_tokens_saved == 0
        assert headroom_engine._session_id == "sess-42"
        # Model kwargs flow through
        assert headroom_engine.model == "claude-opus-4-20250514"

    def test_on_session_end_logs_aggregates(self, headroom_engine, fake_headroom, caplog):
        import logging
        caplog.set_level(logging.INFO, logger="plugins.context_engine.headroom")
        headroom_engine.quiet_mode = False
        headroom_engine.compress([{"role": "user", "content": "x" * 5000}])
        headroom_engine.on_session_end("sess-99", messages=[])
        text = "\n".join(r.message for r in caplog.records)
        assert "sess-99" in text
        assert "1 compression run" in text

    def test_on_session_reset_clears_state(self, headroom_engine, fake_headroom):
        headroom_engine.compress([{"role": "user", "content": "x" * 5000}])
        headroom_engine.on_session_reset()
        assert headroom_engine._total_runs == 0
        assert headroom_engine.compression_count == 0
        assert headroom_engine._last_compress_result is None


# ---------------------------------------------------------------------------
# Model switch
# ---------------------------------------------------------------------------

class TestUpdateModel:
    def test_update_model_uses_registry(self, fake_headroom):
        from plugins.context_engine.headroom import HeadroomContextEngine
        with patch("agent.model_metadata.get_model_context_length", return_value=180000):
            eng = HeadroomContextEngine(model="gpt-4o", quiet_mode=True)
        with patch("agent.model_metadata.get_model_context_length", return_value=1000000):
            eng.update_model(model="claude-sonnet-4-5-20250929", context_length=0, provider="anthropic")
        assert eng.model == "claude-sonnet-4-5-20250929"
        assert eng.context_length == 1_000_000
        assert eng.provider == "anthropic"
        # threshold recalculated
        assert eng.threshold_tokens == int(1_000_000 * eng.threshold_percent)

    def test_update_model_with_empty_model(self, headroom_engine):
        original_ctx = headroom_engine.context_length
        original_thresh = headroom_engine.threshold_tokens
        headroom_engine.update_model(model="", context_length=500_000, provider="")
        # context_length updates from kwarg when no model change
        assert headroom_engine.context_length == 500_000
        assert headroom_engine.threshold_tokens == int(500_000 * headroom_engine.threshold_percent)
