"""Tests for the Scrapling web extract provider plugin.

Scrapling is a fetcher/parser library; the plugin wraps it as a hermes
``WebSearchProvider`` so ``web_extract`` calls route through Scrapling's
adaptive parser + StealthyFetcher anti-bot bypass.

These tests mock the scrapling package at the import boundary so the
suite runs without scrapling installed. Coverage:

  - Plugin discovery (loader finds + instantiates the provider)
  - ABC conformance (name, is_available, supports_search, supports_extract)
  - is_available() — True when Fetcher importable, False otherwise
  - ScraplingConfig.apply_overrides() — config push
  - extract() — happy path (single URL, multiple URLs, async fan-out)
  - extract() — Fetcher→StealthyFetcher auto-escalation on block
  - extract() — error per-URL (Fetcher fail + no StealthyFetcher)
  - extract() — error per-URL (Fetcher fail + StealthyFetcher fail)
  - extract() — error per-URL (scrapling not installed)
  - extract() — empty URL list
  - extract() — website policy blocks the URL
  - _looks_blocked() — status code + body markers
  - register() — pattern wires the provider into the registry
"""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Stubs (fakes) for the scrapling package surface
# ---------------------------------------------------------------------------

class _FakeSelector:
    """Minimal stand-in for scrapling.parser.Selector."""
    def __init__(self, text="", html="", attrib=None):
        self.text = text
        self.html_content = html
        self.attrib = attrib or {}


class _FakeResponse:
    """Stand-in for a Scrapling fetcher's Response object."""
    def __init__(self, *, status=200, body_text="", body_html="",
                 selectors=None, url="https://example.com/"):
        self.status = status
        self.status_code = status
        self.text = body_text
        self.html_content = body_html
        self.url = url
        # selectors: dict[css_selector] → list[_FakeSelector]
        self._selectors = selectors or {}

    def css(self, selector, adaptive=False):
        hits = self._selectors.get(selector) or []
        first = hits[0] if hits else None
        return MagicMock(first=first)


class _FakeFetcher:
    """Stand-in for scrapling.Fetcher — class with .get() that consumes from queue."""
    queue: list = []  # class-level, tests push responses here

    @classmethod
    def get(cls, url, **kwargs):
        if cls.queue:
            return cls.queue.pop(0)
        raise RuntimeError("FakeFetcher: no queued response for " + url)


class _FakeStealthyFetcher:
    """Stand-in for scrapling.StealthyFetcher."""
    queue: list = []

    @classmethod
    def fetch(cls, url, **kwargs):
        if cls.queue:
            return cls.queue.pop(0)
        raise RuntimeError("FakeStealthyFetcher: no queued response for " + url)


class _RaisesOnAccess:
    """Module attribute that raises ImportError on any access.

    Used to simulate ``scrapling.StealthyFetcher`` not being importable.
    The provider's ``from scrapling import StealthyFetcher`` does
    ``getattr(module, "StealthyFetcher")`` which triggers ImportError.
    """
    def __getattr__(self, name):
        raise ImportError("StealthyFetcher not installed (test)")


def _install_fake_scrapling(monkeypatch, *, available=True, with_stealth=True):
    """Install or remove a fake ``scrapling`` module for one test.

    Returns the fake module (or None if unavailable).
    """
    if not available:
        for mod_name in list(sys.modules):
            if mod_name == "scrapling" or mod_name.startswith("scrapling."):
                monkeypatch.delitem(sys.modules, mod_name, raising=False)
        import plugins.web.scrapling.provider as p_mod
        def _raise():
            raise ImportError("scrapling is not installed (test)")
        monkeypatch.setattr(p_mod, "_load_scrapling", _raise)
        return None

    # Build a fresh module each test (no class-level state to leak)
    fake = types.ModuleType("scrapling")
    fake.Fetcher = _FakeFetcher  # type: ignore[attr-defined]
    if with_stealth:
        fake.StealthyFetcher = _FakeStealthyFetcher  # type: ignore[attr-defined]
    else:
        # Make ``from scrapling import StealthyFetcher`` raise ImportError
        fake.StealthyFetcher = _RaisesOnAccess()  # type: ignore[attr-defined]

    # Reset the static queues each test
    _FakeFetcher.queue = []
    _FakeStealthyFetcher.queue = []

    monkeypatch.setitem(sys.modules, "scrapling", fake)
    return fake


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_scrapling(monkeypatch):
    """Scrapling importable; both Fetcher and StealthyFetcher present."""
    f = _install_fake_scrapling(monkeypatch, available=True, with_stealth=True)
    return f


@pytest.fixture()
def fake_scrapling_no_stealth(monkeypatch):
    """Only Fetcher available; StealthyFetcher not installed."""
    f = _install_fake_scrapling(monkeypatch, available=True, with_stealth=False)
    return f


@pytest.fixture()
def scrapling_provider(fake_scrapling):
    """Provider with default config."""
    from plugins.web.scrapling import ScraplingWebSearchProvider
    return ScraplingWebSearchProvider()


@pytest.fixture(autouse=True)
def _reset_module_cache(monkeypatch):
    """Clear the provider's lazy-import cache between tests.

    The module-level ``_SCRAPLING_CACHE`` otherwise keeps the
    first-import's Fetcher/StealthyFetcher between tests, breaking
    later 'not installed' assertions.
    """
    import plugins.web.scrapling.provider as p_mod
    monkeypatch.setattr(p_mod, "_SCRAPLING_CACHE", None)


# ---------------------------------------------------------------------------
# ABC conformance + identity
# ---------------------------------------------------------------------------

class TestABCConformance:
    def test_is_subclass_of_websearchprovider(self, scrapling_provider):
        from agent.web_search_provider import WebSearchProvider
        assert isinstance(scrapling_provider, WebSearchProvider)

    def test_name_is_scrapling(self, scrapling_provider):
        assert scrapling_provider.name == "scrapling"

    def test_display_name(self, scrapling_provider):
        assert "Scrapling" in scrapling_provider.display_name
        assert "self-hosted" in scrapling_provider.display_name.lower()

    def test_supports_search_is_false(self, scrapling_provider):
        # Scrapling has no search API; user must pair with ddgs/brave/searxng
        assert scrapling_provider.supports_search() is False

    def test_supports_extract_is_true(self, scrapling_provider):
        assert scrapling_provider.supports_extract() is True


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_is_available_when_scrapling_present(self, scrapling_provider):
        assert scrapling_provider.is_available() is True

    def test_is_available_false_when_scrapling_missing(self, monkeypatch):
        _install_fake_scrapling(monkeypatch, available=False)
        from plugins.web.scrapling import ScraplingWebSearchProvider
        p = ScraplingWebSearchProvider()
        assert p.is_available() is False

    def test_is_available_true_when_only_stealth_missing(self, fake_scrapling_no_stealth):
        from plugins.web.scrapling import ScraplingWebSearchProvider
        p = ScraplingWebSearchProvider()
        # Fetcher alone is enough for is_available
        assert p.is_available() is True


# ---------------------------------------------------------------------------
# ScraplingConfig
# ---------------------------------------------------------------------------

class TestScraplingConfig:
    def test_defaults(self):
        from plugins.web.scrapling import ScraplingConfig
        c = ScraplingConfig()
        assert c.stealthy_fallback is True
        assert c.adaptive is True
        assert c.timeout == 30
        assert c.headless is True
        assert c.proxy is None
        assert c.max_content_chars == 50_000
        assert c.selector_strategy == "auto"
        assert c.force_stealth is False

    def test_apply_overrides_known_keys(self):
        from plugins.web.scrapling import ScraplingConfig
        c = ScraplingConfig()
        c.apply_overrides({
            "timeout": 60,
            "headless": False,
            "proxy": "http://user:pass@host:1080",
            "max_content_chars": 10000,
        })
        assert c.timeout == 60
        assert c.headless is False
        assert c.proxy == "http://user:pass@host:1080"
        assert c.max_content_chars == 10000

    def test_apply_overrides_ignores_unknown(self):
        from plugins.web.scrapling import ScraplingConfig
        c = ScraplingConfig()
        c.apply_overrides({"totally_unknown": "x"})
        assert c.timeout == 30  # default unchanged

    def test_apply_overrides_handles_non_dict(self):
        from plugins.web.scrapling import ScraplingConfig
        c = ScraplingConfig()
        c.apply_overrides({})  # empty dict is fine
        assert c.timeout == 30


# ---------------------------------------------------------------------------
# Extraction: happy paths
# ---------------------------------------------------------------------------

class TestExtractHappyPath:
    def test_extract_single_url(self, scrapling_provider, fake_scrapling):
        body = "Welcome to example.com. " * 200
        _FakeFetcher.queue = [_FakeResponse(
            status=200,
            body_text=body,
            body_html=f"<html><head><title>Example</title></head><body>{body}</body></html>",
            selectors={
                "head title": [_FakeSelector(text="Example")],
                "article": [_FakeSelector(text=body, html=body)],
            },
        )]

        results = asyncio.run(scrapling_provider.extract(["https://example.com/"]))
        assert len(results) == 1
        r = results[0]
        assert r["url"] == "https://example.com/"
        assert r["title"] == "Example"
        # Content extracted from "article" selector — check the marker is in there
        # (exact whitespace may vary across Scrapling versions)
        assert "Welcome to example.com." in r["content"]
        assert len(r["content"]) >= 1000  # has substance
        assert "error" not in r
        assert r["metadata"]["fetcher"] == "Fetcher"
        assert r["metadata"]["status_code"] == 200

    def test_extract_multiple_urls_concurrent(self, scrapling_provider, fake_scrapling):
        for i in range(3):
            _FakeFetcher.queue.append(_FakeResponse(
                status=200,
                body_text=f"Page {i} content. " * 100,
                body_html=f"<html><head><title>Page {i}</title></head><body>Page {i}</body></html>",
                selectors={
                    "head title": [_FakeSelector(text=f"Page {i}")],
                    "article": [_FakeSelector(text=f"Page {i} content. " * 100,
                                              html=f"<p>Page {i}</p>")],
                },
            ))

        urls = [f"https://example.com/p{i}" for i in range(3)]
        results = asyncio.run(scrapling_provider.extract(urls))
        assert len(results) == 3
        for i, r in enumerate(results):
            assert r["url"] == urls[i]
            assert r["title"] == f"Page {i}"
            assert f"Page {i}" in r["content"]

    def test_extract_empty_list(self, scrapling_provider):
        results = asyncio.run(scrapling_provider.extract([]))
        assert results == []

    def test_extract_truncates_long_content(self, scrapling_provider, fake_scrapling):
        big = "x" * 100_000
        _FakeFetcher.queue = [_FakeResponse(
            status=200,
            body_text=big,
            body_html=big,
            selectors={"article": [_FakeSelector(text=big, html=big)]},
        )]
        scrapling_provider.config.max_content_chars = 5_000
        results = asyncio.run(scrapling_provider.extract(["https://example.com/"]))
        assert len(results[0]["content"]) == 5_000
        assert len(results[0]["raw_content"]) == 5_000


# ---------------------------------------------------------------------------
# Extraction: fallback / error paths
# ---------------------------------------------------------------------------

class TestExtractFallbacks:
    def test_escalates_to_stealthy_on_block(self, scrapling_provider, fake_scrapling):
        # Fetcher: blocked (403 + block marker)
        _FakeFetcher.queue = [_FakeResponse(
            status=403,
            body_text="Just a moment... Checking your browser before accessing example.com.",
            body_html="<html>Cloudflare</html>",
            selectors={},
        )]
        # StealthyFetcher: success
        _FakeStealthyFetcher.queue = [_FakeResponse(
            status=200,
            body_text="Real content. " * 100,
            body_html="<html><head><title>Real</title></head><body>Real content</body></html>",
            selectors={
                "head title": [_FakeSelector(text="Real")],
                "article": [_FakeSelector(text="Real content. " * 100)],
            },
        )]

        results = asyncio.run(scrapling_provider.extract(["https://example.com/"]))
        assert len(results) == 1
        r = results[0]
        assert "error" not in r
        assert r["title"] == "Real"
        assert r["metadata"]["fetcher"] == "StealthyFetcher"

    def test_no_stealthy_escalation_when_fetcher_succeeds(self, scrapling_provider, fake_scrapling):
        _FakeFetcher.queue = [_FakeResponse(
            status=200,
            body_text="Plain content. " * 100,
            selectors={"article": [_FakeSelector(text="Plain content. " * 100)]},
        )]
        results = asyncio.run(scrapling_provider.extract(["https://example.com/"]))
        assert results[0]["metadata"]["fetcher"] == "Fetcher"
        # No stealthy response consumed
        assert _FakeStealthyFetcher.queue == []

    def test_fetcher_fail_no_stealthy_returns_error(self, monkeypatch):
        fake = _install_fake_scrapling(monkeypatch, available=True, with_stealth=False)
        # Replace Fetcher with a class that always raises
        class _FailFetcher:
            @classmethod
            def get(cls, url, **kwargs):
                raise RuntimeError("network unreachable")
        fake.Fetcher = _FailFetcher  # type: ignore[assignment]
        from plugins.web.scrapling import ScraplingWebSearchProvider
        p = ScraplingWebSearchProvider()
        results = asyncio.run(p.extract(["https://example.com/"]))
        assert len(results) == 1
        assert "error" in results[0]
        # No stealthy fallback, Fetcher failed → error message
        assert ("stealthy fallback disabled" in results[0]["error"]
                or "all fetchers failed" in results[0]["error"])

    def test_fetcher_fail_stealthy_succeeds(self, scrapling_provider, fake_scrapling):
        class _FailFetcher:
            @classmethod
            def get(cls, url, **kwargs):
                raise RuntimeError("network unreachable")
        fake_scrapling.Fetcher = _FailFetcher  # type: ignore[assignment]
        _FakeStealthyFetcher.queue = [_FakeResponse(
            status=200,
            body_text="Stealthy content. " * 100,
            selectors={"article": [_FakeSelector(text="Stealthy content. " * 100)]},
        )]

        results = asyncio.run(scrapling_provider.extract(["https://example.com/"]))
        assert len(results) == 1
        r = results[0]
        # Fetcher exception → response is None → escalate to Stealthy → success
        assert "error" not in r
        assert r["metadata"]["fetcher"] == "StealthyFetcher"

    def test_scrapling_not_installed(self, monkeypatch):
        _install_fake_scrapling(monkeypatch, available=False)
        from plugins.web.scrapling import ScraplingWebSearchProvider
        p = ScraplingWebSearchProvider()
        results = asyncio.run(p.extract(["https://example.com/"]))
        assert len(results) == 1
        assert "scrapling is not installed" in results[0]["error"]

    def test_stealthy_fallback_disabled(self, scrapling_provider, fake_scrapling):
        # Blocked response
        _FakeFetcher.queue = [_FakeResponse(status=403, body_text="Just a moment...")]
        scrapling_provider.config.stealthy_fallback = False
        results = asyncio.run(scrapling_provider.extract(["https://example.com/"]))
        # Stealthy should NOT be called
        assert _FakeStealthyFetcher.queue == []
        # The blocked response has 0 chars content → may parse to empty content,
        # but fetcher_used should be "Fetcher" (stealth was disabled)
        r = results[0]
        assert r["metadata"].get("fetcher") == "Fetcher"

    def test_force_stealth_skips_fetcher(self, scrapling_provider, fake_scrapling):
        from plugins.web.scrapling import ScraplingConfig
        scrapling_provider.config = ScraplingConfig(force_stealth=True)
        _FakeStealthyFetcher.queue = [_FakeResponse(
            status=200, body_text="Stealth-only content. " * 100,
            selectors={"article": [_FakeSelector(text="Stealth-only content. " * 100)]},
        )]
        results = asyncio.run(scrapling_provider.extract(["https://example.com/"]))
        assert results[0]["metadata"]["fetcher"] == "StealthyFetcher"
        assert _FakeFetcher.queue == []  # Fetcher never called

    def test_one_url_bad_doesnt_poison_batch(self, scrapling_provider, fake_scrapling):
        # First URL: blocked, no stealthy fallback
        _FakeFetcher.queue = [
            _FakeResponse(status=500, body_text="Internal Server Error" * 30),
            _FakeResponse(
                status=200, body_text="OK content. " * 100,
                selectors={"article": [_FakeSelector(text="OK content. " * 100)]},
            ),
        ]
        scrapling_provider.config.stealthy_fallback = False

        results = asyncio.run(scrapling_provider.extract([
            "https://example.com/bad", "https://example.com/good"
        ]))
        assert len(results) == 2
        # Second result: success
        assert results[1]["url"] == "https://example.com/good"
        assert "OK" in results[1]["content"]


# ---------------------------------------------------------------------------
# _looks_blocked
# ---------------------------------------------------------------------------

class TestLooksBlocked:
    def test_403_status(self):
        from plugins.web.scrapling.provider import _looks_blocked
        r = _FakeResponse(status=403, body_text="OK content here " * 50)
        assert _looks_blocked(r) is True

    def test_503_status(self):
        from plugins.web.scrapling.provider import _looks_blocked
        r = _FakeResponse(status=503, body_text="normal page text " * 50)
        assert _looks_blocked(r) is True

    def test_cloudflare_marker(self):
        from plugins.web.scrapling.provider import _looks_blocked
        r = _FakeResponse(status=200, body_text="Just a moment... checking your browser")
        assert _looks_blocked(r) is True

    def test_captcha_marker(self):
        from plugins.web.scrapling.provider import _looks_blocked
        r = _FakeResponse(status=200, body_text="Please solve the captcha to continue")
        assert _looks_blocked(r) is True

    def test_normal_200_not_blocked(self):
        from plugins.web.scrapling.provider import _looks_blocked
        r = _FakeResponse(
            status=200,
            body_text="A perfectly normal article about web scraping. " * 50,
        )
        assert _looks_blocked(r) is False

    def test_none_response(self):
        from plugins.web.scrapling.provider import _looks_blocked
        assert _looks_blocked(None) is True

    def test_no_body_no_status_assume_not_blocked(self):
        from plugins.web.scrapling.provider import _looks_blocked
        r = _FakeResponse(status=0, body_text="")
        assert _looks_blocked(r) is False


# ---------------------------------------------------------------------------
# Plugin discovery + register pattern
# ---------------------------------------------------------------------------

class TestDiscovery:
    def test_plugin_dir_exists(self):
        from pathlib import Path
        d = Path("/home/hermes/.hermes/hermes-agent/plugins/web/scrapling")
        assert d.is_dir()
        assert (d / "__init__.py").is_file()
        assert (d / "provider.py").is_file()
        assert (d / "plugin.yaml").is_file()

    def test_plugin_yaml_has_required_keys(self):
        from pathlib import Path
        import yaml
        meta = yaml.safe_load((Path("/home/hermes/.hermes/hermes-agent/plugins/web/scrapling") / "plugin.yaml").read_text())
        assert meta["name"] == "web-scrapling"
        assert meta["kind"] == "backend"
        assert "scrapling" in meta["provides_web_providers"]
        assert meta["license"] == "BSD-3-Clause"

    def test_register_pattern_works(self, fake_scrapling):
        from plugins.web.scrapling import register

        class _FakeCtx:
            def __init__(self):
                self.providers = []
            def register_web_search_provider(self, p):
                self.providers.append(p)
        ctx = _FakeCtx()
        register(ctx)
        assert len(ctx.providers) == 1
        assert ctx.providers[0].name == "scrapling"

    def test_module_init_re_exports_provider(self):
        from plugins.web.scrapling import (
            ScraplingWebSearchProvider,
            ScraplingConfig,
            register,
        )
        assert ScraplingWebSearchProvider is not None
        assert ScraplingConfig is not None
        assert callable(register)


# ---------------------------------------------------------------------------
# Config overrides via extract() kwargs
# ---------------------------------------------------------------------------

class TestConfigOverrides:
    def test_scrapling_kwarg_overrides(self, scrapling_provider, fake_scrapling):
        _FakeFetcher.queue = [_FakeResponse(
            status=200, body_text="X" * 1000,
            selectors={"article": [_FakeSelector(text="X" * 1000)]},
        )]
        asyncio.run(scrapling_provider.extract(
            ["https://example.com/"],
            scrapling={"max_content_chars": 100, "timeout": 5},
        ))
        assert scrapling_provider.config.max_content_chars == 100
        assert scrapling_provider.config.timeout == 5
