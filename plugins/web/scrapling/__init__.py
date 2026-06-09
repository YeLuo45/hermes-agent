"""Scrapling web extract provider — bundled, auto-loaded.

Mirrors the ``plugins/web/<vendor>/`` layout used by firecrawl/ddgs/
brave_free/...: ``provider.py`` holds the provider class; this
``__init__.py::register`` instantiates and registers it.
"""

from __future__ import annotations

from plugins.web.scrapling.provider import (
    ScraplingConfig,
    ScraplingWebSearchProvider,
    _looks_blocked,
)


def register(ctx) -> None:
    """Register the Scrapling provider with the plugin context.

    ``ctx`` is the ``PluginContext`` provided by the plugin loader.
    The provider is instantiated with default config — per-session
    overrides come from ``web.scrapling.*`` in ``config.yaml`` (see
    :meth:`ScraplingConfig.apply_overrides`).
    """
    ctx.register_web_search_provider(ScraplingWebSearchProvider())


__all__ = [
    "ScraplingWebSearchProvider",
    "ScraplingConfig",
    "register",
]
