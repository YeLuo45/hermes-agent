"""Scrapling web extract provider for Hermes Agent.

Extract-only backend (Scrapling has no search API; pair with ddgs/brave/
searxng for search). Built around the same :class:`WebSearchProvider`
ABC the other ``plugins/web/`` vendors use, so wiring it in is a
config-only change::

    # ~/.hermes/config.yaml
    web:
      extract_backend: "scrapling"     # use Scrapling for web_extract calls
      search_backend: "ddgs"           # (still need a search provider)
      scrapling:
        stealthy_fallback: true        # auto-escalate to StealthyFetcher on block
        adaptive: true                 # survive website redesigns
        timeout: 30
        headless: true
        max_content_chars: 50000

Requires ``pip install "scrapling[all]>=0.4.8"`` and (for stealth mode)
``scrapling install --force`` to download browser dependencies. The
provider is **self-hosted** — no API keys, no cloud calls.

Why use it over Firecrawl?
--------------------------
1. **Self-hosted & free.** No API keys, no usage caps. Runs entirely on
   your machine.
2. **Adaptive parser.** :meth:`Response.css(selector, adaptive=True)`
   re-learns selectors from auto-saved examples when a site redesigns.
   Your scrapers don't break the next time a CSS class gets renamed.
3. **Anti-bot bypass out of the box.** :class:`StealthyFetcher` defeats
   Cloudflare Turnstile, Incapsula, and most fingerprinting heuristics
   without external solver services.
4. **Two fetchers, one provider.** :class:`Fetcher` (fast HTTP, no
   browser) handles 80% of pages. :class:`StealthyFetcher` (headless
   Chromium with stealth patches) escalates automatically on the 20%
   that need it. The ``stealthy_fallback`` knob toggles the escalation.
5. **BSD-3 licensed.** Permissive; use it in commercial products.

Trade-offs
----------
* Single-threaded by default (Sync :class:`Fetcher` + :class:`StealthyFetcher`).
  The plugin wraps per-URL calls in :func:`asyncio.to_thread` so multiple
  URLs in one extract() invocation still run concurrently.
* StealthyFetcher needs Playwright + a Chromium download (~150MB).
* No built-in web search; you still need a search provider to *find*
  URLs, then Scrapling to *extract* from them.

How to enable
-------------
Add to ``~/.hermes/config.yaml``::

    web:
      extract_backend: "scrapling"
      scrapling:
        stealthy_fallback: true
        adaptive: true
        timeout: 30
        headless: true

Then::

    pip install "scrapling[all]>=0.4.8"
    scrapling install --force

References
----------
- Scrapling repo: https://github.com/D4Vinci/Scrapling
- Hermes ABC: ``agent/web_search_provider.py``
- Hermes registry: ``agent/web_search_registry.py``
- Provider contract example: ``plugins/web/firecrawl/provider.py``
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.web_search_provider import WebSearchProvider
from tools.website_policy import check_website_access

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy-import shim for scrapling
# ---------------------------------------------------------------------------
# Scrapling pulls Playwright + browser-automation deps on import (stealth
# fetcher path). We keep the provider importable even when scrapling is
# not installed so plugins can be enumerated without forcing an install.
# ``is_available()`` does the real check; ``_load_scrapling()`` is the
# lazy hook used by ``extract()``.

def _load_scrapling() -> Dict[str, Any]:
    """Import scrapling's fetchers lazily and return them in a dict.

    Returns ``{"Fetcher": cls, "StealthyFetcher": cls}`` (or just
    ``Fetcher`` if stealth isn't installed). Raises ``ImportError``
    with an actionable message if scrapling itself is missing.

    Cached on first successful import so we don't pay the cost again.
    """
    global _SCRAPLING_CACHE
    if _SCRAPLING_CACHE is not None:
        return _SCRAPLING_CACHE

    cache: Dict[str, Any] = {}
    try:
        from scrapling import Fetcher  # type: ignore
        cache["Fetcher"] = Fetcher
    except ImportError as exc:
        raise ImportError(
            "scrapling is not installed. Run: pip install 'scrapling[all]>=0.4.8' "
            "then 'scrapling install --force' for browser deps. "
            f"Original error: {exc}"
        ) from exc

    # StealthyFetcher is optional — only present if [all] / [stealth] is installed.
    try:
        from scrapling import StealthyFetcher  # type: ignore
        cache["StealthyFetcher"] = StealthyFetcher
    except ImportError:
        cache["StealthyFetcher"] = None

    _SCRAPLING_CACHE = cache
    return cache


_SCRAPLING_CACHE: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ScraplingConfig:
    """Tunable knobs for the Scrapling provider.

    Defaults are tuned for "scrape a normal blog/news page reliably":
    30s timeout, 50K char content ceiling, auto-escalate to stealth on
    block, adaptive parser on (survives redesigns). Override per-session
    via ``web.scrapling.*`` in config.yaml.
    """

    # Auto-escalate from Fetcher → StealthyFetcher when a block is detected
    stealthy_fallback: bool = True

    # Adaptive parser: re-learn selectors from auto-saved examples on miss
    adaptive: bool = True

    # Per-request timeout in seconds
    timeout: int = 30

    # Run headless Chromium (only used by StealthyFetcher)
    headless: bool = True

    # Optional HTTP/HTTPS proxy URL (e.g. http://user:pass@host:port)
    proxy: Optional[str] = None

    # Optional user data dir for persistent Chromium profile
    user_data_dir: Optional[str] = None

    # Truncate extracted content to this many chars (avoids blowing context)
    max_content_chars: int = 50_000

    # Selector strategy: "auto" (try article/main → body), or explicit CSS
    selector_strategy: str = "auto"

    # If set, only run StealthyFetcher (skip Fetcher fast path)
    force_stealth: bool = False

    def apply_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply config.yaml overrides; ignore unknown keys silently."""
        if not isinstance(overrides, dict):
            return
        for key, value in overrides.items():
            if hasattr(self, key):
                setattr(self, key, value)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class ScraplingWebSearchProvider(WebSearchProvider):
    """Self-hosted web extract backend powered by Scrapling.

    Implements the ``WebSearchProvider`` ABC. **Extract-only** — Scrapling
    is a fetcher/parser library, not a search engine. ``supports_search``
    returns ``False`` so the registry falls through to ddgs/brave/searxng
    for search calls. ``supports_extract`` returns ``True``; ``extract()``
    is the main entry point.

    Per-URL fetch strategy (when ``stealthy_fallback=True``):

      1. Try ``Fetcher.get(url)`` — fast HTTP, no browser.
      2. Detect block markers in the response (403/503, captcha text,
         empty body, <title>Just a moment</title>).
      3. If blocked AND StealthyFetcher is available, escalate to
         ``StealthyFetcher.fetch(url, headless=...)``.
      4. Parse with adaptive CSS selectors (re-learns on miss).
      5. Truncate content to ``max_content_chars``.
    """

    @property
    def name(self) -> str:
        return "scrapling"

    @property
    def display_name(self) -> str:
        return "Scrapling (adaptive self-hosted extract)"

    def __init__(self, config: Optional[ScraplingConfig] = None) -> None:
        self.config = config or ScraplingConfig()

    # -- ABC: availability ------------------------------------------------

    def is_available(self) -> bool:
        """True when scrapling is importable. Does NOT require stealth."""
        try:
            fetchers = _load_scrapling()
            return fetchers.get("Fetcher") is not None
        except ImportError:
            return False

    def supports_search(self) -> bool:
        """False. Scrapling has no search API — use ddgs/brave/searxng."""
        return False

    def supports_extract(self) -> bool:
        return True

    # -- ABC: extract -----------------------------------------------------

    async def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Extract content from one or more URLs.

        Runs per-URL fetches concurrently via ``asyncio.to_thread`` so a
        10-URL batch completes in roughly the time of the slowest page
        (not the sum). Per-URL failures are isolated — one bad URL
        doesn't poison the batch.

        Returns a list of result dicts matching the legacy contract::

            [{
                "url": str,
                "title": str,
                "content": str,        # cleaned main text
                "raw_content": str,    # raw HTML, truncated
                "metadata": dict,      # {status_code, fetcher, ...}
                "error": str,          # only on per-URL failure
            }, ...]
        """
        if not urls:
            return []

        # Apply any kwargs that look like config overrides
        cfg_overrides = kwargs.get("scrapling") or kwargs.get("config_overrides")
        if isinstance(cfg_overrides, dict):
            self.config.apply_overrides(cfg_overrides)

        # Fan out
        results = await asyncio.gather(
            *(self._extract_one(url) for url in urls),
            return_exceptions=False,
        )
        return results

    # -- Per-URL extraction ----------------------------------------------

    async def _extract_one(self, url: str) -> Dict[str, Any]:
        """Fetch + extract a single URL with auto-escalation."""
        # SSRF / website policy gate (matches Firecrawl's behavior)
        try:
            allowed = check_website_access(url)
        except Exception as exc:  # never let the gate crash extraction
            logger.debug("website policy check failed for %s: %s", url, exc)
            allowed = True
        if not allowed:
            return self._error_result(url, "blocked by website policy")

        try:
            fetchers = _load_scrapling()
        except ImportError as exc:
            return self._error_result(url, str(exc))

        # Fast path: Fetcher (no browser)
        response = None
        fetcher_used = "Fetcher"
        if not self.config.force_stealth:
            try:
                response = await asyncio.to_thread(
                    self._fetcher_get, fetchers["Fetcher"], url
                )
            except Exception as exc:
                logger.debug("Fetcher.get failed for %s: %s", url, exc)
                response = None

        # Detect block and escalate to StealthyFetcher
        if response is None or _looks_blocked(response):
            if self.config.stealthy_fallback and fetchers.get("StealthyFetcher"):
                logger.info("Scrapling: escalating %s to StealthyFetcher", url)
                try:
                    response = await asyncio.to_thread(
                        self._stealthy_fetch, fetchers["StealthyFetcher"], url
                    )
                    fetcher_used = "StealthyFetcher"
                except Exception as exc:
                    logger.warning("StealthyFetcher.fetch failed for %s: %s", url, exc)
                    if response is None:
                        return self._error_result(
                            url, f"all fetchers failed: {exc}"
                        )
            elif response is None:
                return self._error_result(url, "Fetcher failed and stealthy fallback disabled")

        if response is None:
            return self._error_result(url, "no response from any fetcher")

        # Parse
        try:
            parsed = self._parse_response(response, url)
        except Exception as exc:
            logger.warning("Scrapling parse failed for %s: %s", url, exc)
            return self._error_result(url, f"parse error: {exc}")

        parsed.setdefault("metadata", {})
        parsed["metadata"].update({
            "fetcher": fetcher_used,
            "adaptive": self.config.adaptive,
        })
        return parsed

    # -- Fetcher helpers --------------------------------------------------

    def _fetcher_get(self, FetcherCls: Any, url: str) -> Any:
        """Wrap ``Fetcher.get`` with our config + a timeout guard."""
        kwargs: Dict[str, Any] = {
            "timeout": self.config.timeout,
            "stealthy_headers": True,  # Fetcher-level stealth hint
        }
        if self.config.proxy:
            kwargs["proxy"] = self.config.proxy
        return FetcherCls.get(url, **kwargs)

    def _stealthy_fetch(self, StealthyFetcherCls: Any, url: str) -> Any:
        """Wrap ``StealthyFetcher.fetch`` with our config."""
        kwargs: Dict[str, Any] = {
            "headless": self.config.headless,
            "network_idle": True,
            "timeout": self.config.timeout * 1000,  # ms vs seconds
        }
        if self.config.proxy:
            kwargs["proxy"] = self.config.proxy
        if self.config.user_data_dir:
            kwargs["user_data_dir"] = self.config.user_data_dir
        return StealthyFetcherCls.fetch(url, **kwargs)

    # -- Parser -----------------------------------------------------------

    def _parse_response(self, response: Any, url: str) -> Dict[str, Any]:
        """Extract title + main content from a Scrapling ``Response``."""
        title = self._extract_title(response)
        content_text, content_html = self._extract_main(response)
        # Truncate
        if len(content_text) > self.config.max_content_chars:
            content_text = content_text[: self.config.max_content_chars]
        if len(content_html) > self.config.max_content_chars:
            content_html = content_html[: self.config.max_content_chars]
        return {
            "url": url,
            "title": title or "",
            "content": content_text,
            "raw_content": content_html,
            "metadata": {
                "status_code": getattr(response, "status", None) or getattr(response, "status_code", None),
                "url_final": getattr(response, "url", url),
            },
        }

    def _extract_title(self, response: Any) -> Optional[str]:
        """Best-effort title extraction, ordered by reliability."""
        for sel in ("head title", "head meta[property='og:title']", "h1"):
            try:
                if sel.startswith("head meta"):
                    # og:title: pull the `content` attribute
                    el = response.css(sel, adaptive=self.config.adaptive).first
                    if el is not None:
                        content = el.attrib.get("content") if hasattr(el, "attrib") else None
                        if content:
                            return content.strip()
                else:
                    el = response.css(sel, adaptive=self.config.adaptive).first
                    if el is not None and el.text:
                        return el.text.strip()
            except Exception as exc:
                logger.debug("title selector %r failed: %s", sel, exc)
        return None

    def _extract_main(self, response: Any) -> tuple[str, str]:
        """Return ``(plain_text, raw_html)`` for the main content area.

        Strategy: try article/main/[role=main] → body. The first selector
        with substantial content wins. ``adaptive=True`` re-derives the
        selector from saved fingerprints when sites redesign.
        """
        # Selector candidates, in preference order
        candidates = (
            "article",
            "main",
            "[role='main']",
            "#content",
            ".content",
            "#main",
            ".post",
            ".article",
            "body",
        )

        for sel in candidates:
            try:
                el = response.css(sel, adaptive=self.config.adaptive).first
            except Exception as exc:
                logger.debug("main selector %r raised: %s", sel, exc)
                continue
            if el is None:
                continue
            text = (el.text or "").strip()
            if len(text) >= 200:  # need at least *some* substance
                html = el.html_content if hasattr(el, "html_content") else ""
                return text, html or ""

        # Fallback: full body text
        try:
            body = response.css("body", adaptive=False).first
        except Exception:
            body = None
        if body is not None:
            return (body.text or "").strip(), (body.html_content or "") if hasattr(body, "html_content") else ""

        # Last resort
        return "", ""

    # -- Errors -----------------------------------------------------------

    @staticmethod
    def _error_result(url: str, message: str) -> Dict[str, Any]:
        """Build a per-URL failure record. Matches the legacy error contract."""
        return {
            "url": url,
            "title": "",
            "content": "",
            "raw_content": "",
            "metadata": {},
            "error": message,
        }


# ---------------------------------------------------------------------------
# Block detection
# ---------------------------------------------------------------------------

_BLOCK_STATUS_CODES = {401, 403, 407, 429, 503, 520, 521, 522, 523, 524}
_BLOCK_TEXT_MARKERS = (
    "just a moment",
    "attention required",
    "checking your browser",
    "cloudflare",
    "access denied",
    "please enable cookies",
    "are you a human",
    "captcha",
    "cf-chl-bypass",
    "rate limit",
)


def _looks_blocked(response: Any) -> bool:
    """Heuristic: did the Fetcher hit an anti-bot wall?

    Returns True when the response status is in ``_BLOCK_STATUS_CODES``
    OR the body contains well-known block-page markers. Used to decide
    whether to escalate to StealthyFetcher.
    """
    if response is None:
        return True
    status = (
        getattr(response, "status", None)
        or getattr(response, "status_code", None)
    )
    if isinstance(status, int) and status in _BLOCK_STATUS_CODES:
        return True

    # Inspect the body for block markers
    body_text = ""
    try:
        # Response.html_content or .text gives the raw/cleaned text
        body_text = (getattr(response, "text", "") or "").lower()
    except Exception:
        pass
    if not body_text:
        try:
            body_text = (getattr(response, "html_content", "") or "").lower()
        except Exception:
            pass
    if not body_text:
        return False  # can't tell — assume not blocked

    for marker in _BLOCK_TEXT_MARKERS:
        if marker in body_text:
            return True
    return False


# ---------------------------------------------------------------------------
# Plugin registration (lives in plugins/web/scrapling/__init__.py)
# ---------------------------------------------------------------------------
# Mirrors the ``register(ctx)`` pattern used by every other web
# plugin (firecrawl, ddgs, brave_free, …). The loader's
# ``PluginContext`` calls ``register_web_search_provider`` to add us
# to the registry; the dispatcher in ``agent/web_search_registry.py``
# picks us up when ``web.extract_backend: scrapling`` is set.
