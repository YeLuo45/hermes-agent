"""Tests for hermes_cli.mcp_catalog — aitoearn entry.

Covers the schema (so the manifest stays parsable across schema versions),
the region defaulting (international vs China), the env-var surface
(AITO_EARN_API_KEY is secret; AITO_EARN_BASE_URL is user-editable), and
the default config-block shape that the catalog's `install_entry()` would
write into ``~/.hermes/config.yaml``.

These tests don't talk to aitoearn.ai — they only exercise the manifest
file and the catalog parser.  No network, no real auth.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _default_mock_probe(monkeypatch):
    """Don't run real probes — manifest-only tests."""
    import hermes_cli.mcp_catalog as mc

    monkeypatch.setattr(mc, "_probe_tools", lambda name: None)


@pytest.fixture(autouse=True)
def _isolate_hermes_home(tmp_path, monkeypatch):
    """Redirect config I/O to a temp HERMES_HOME."""
    hh = tmp_path / "hermes-home"
    hh.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hh))
    monkeypatch.setattr("hermes_cli.config.get_hermes_home", lambda: hh)
    monkeypatch.setattr("hermes_cli.config.get_config_path", lambda: hh / "config.yaml")
    monkeypatch.setattr("hermes_cli.config.get_env_path", lambda: hh / ".env")
    monkeypatch.setattr("hermes_constants.get_hermes_home", lambda: hh)
    return hh


@pytest.fixture
def catalog_dir(tmp_path, monkeypatch):
    """Provide an isolated optional-mcps/ directory for the test."""
    cat = tmp_path / "optional-mcps"
    cat.mkdir()
    monkeypatch.setenv("HERMES_OPTIONAL_MCPS", str(cat))
    return cat


@pytest.fixture
def aitoearn_manifest_path() -> Path:
    """Path to the real aitoearn manifest shipped with the repo."""
    # This file lives in <repo>/optional-mcps/aitoearn/manifest.yaml.
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "optional-mcps" / "aitoearn" / "manifest.yaml"


# ---------------------------------------------------------------------------
# Schema / parsing
# ---------------------------------------------------------------------------


class TestAitoearnManifestSchema:
    """The shipped manifest must round-trip through the catalog parser."""

    def test_manifest_file_exists(self, aitoearn_manifest_path):
        assert aitoearn_manifest_path.is_file(), (
            f"aitoearn manifest missing at {aitoearn_manifest_path}"
        )

    def test_manifest_parses_cleanly(self, aitoearn_manifest_path):
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        assert entry.name == "aitoearn"
        assert entry.transport.type == "http"
        assert entry.transport.url == "https://aitoearn.ai/api/unified/mcp"
        assert entry.auth.type == "api_key"

    def test_manifest_version_supported(self, aitoearn_manifest_path):
        """Bump this test if we ever need v2 of the manifest schema."""
        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        from hermes_cli.mcp_catalog import _MANIFEST_VERSION

        assert data["manifest_version"] == _MANIFEST_VERSION

    def test_name_matches_catalog_id_regex(self, aitoearn_manifest_path):
        """Catalog name regex is ``^[A-Za-z0-9_-]+$``."""
        import re

        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        assert re.match(r"^[A-Za-z0-9_-]+$", data["name"])

    def test_description_non_empty(self, aitoearn_manifest_path):
        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        assert data.get("description", "").strip()

    def test_source_points_to_upstream(self, aitoearn_manifest_path):
        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        assert data["source"].startswith("https://github.com/yikart/AiToEarn")

    def test_post_install_present(self, aitoearn_manifest_path):
        """post_install is user-facing copy surfaced after install."""
        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        post = data.get("post_install", "")
        assert "aitoearn" in post.lower()
        # Must mention the region switch
        assert "aitoearn.cn" in post or "region" in post.lower()


# ---------------------------------------------------------------------------
# Transport + auth shape
# ---------------------------------------------------------------------------


class TestAitoearnTransport:
    def test_uses_http_transport_not_stdio(self, aitoearn_manifest_path):
        """AiToEarn is a SaaS MCP — we hit the remote endpoint, no local install."""
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        assert entry.transport.type == "http"
        assert entry.transport.command is None
        assert entry.transport.args == []

    def test_url_uses_international_region_by_default(self, aitoearn_manifest_path):
        """Default URL = international.  China override happens at install time."""
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        assert entry.transport.url.startswith("https://aitoearn.")
        assert "aitoearn.ai" in entry.transport.url
        assert "aitoearn.cn" not in entry.transport.url  # default is intl

    def test_url_ends_with_mcp_endpoint(self, aitoearn_manifest_path):
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        assert entry.transport.url.endswith("/api/unified/mcp")

    def test_no_install_block(self, aitoearn_manifest_path):
        """No git clone, no bootstrap — the server runs on aitoearn.ai."""
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        assert entry.install is None


class TestAitoearnAuth:
    def test_uses_api_key_auth_not_oauth(self, aitoearn_manifest_path):
        """AiToEarn ships a static API key — no OAuth flow needed."""
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        assert entry.auth.type == "api_key"
        assert entry.auth.provider is None  # not provider-mediated OAuth

    def test_api_key_env_var_required_and_secret(self, aitoearn_manifest_path):
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        api_key = next(
            (e for e in entry.auth.env if e.name == "AITO_EARN_API_KEY"), None
        )
        assert api_key is not None, "AITO_EARN_API_KEY env var must be declared"
        assert api_key.required is True
        assert api_key.secret is True
        # The prompt should mention how to get a key
        prompt_lower = api_key.prompt.lower()
        assert "api" in prompt_lower and "key" in prompt_lower

    def test_base_url_env_var_editable(self, aitoearn_manifest_path):
        """AITO_EARN_BASE_URL is the region switch — non-secret, with default."""
        from hermes_cli.mcp_catalog import _parse_manifest

        entry = _parse_manifest(aitoearn_manifest_path)
        base_url = next(
            (e for e in entry.auth.env if e.name == "AITO_EARN_BASE_URL"), None
        )
        assert base_url is not None, "AITO_EARN_BASE_URL env var must be declared"
        assert base_url.secret is False
        assert base_url.default  # defaulting to international
        assert "aitoearn.ai" in base_url.default

    def test_env_var_names_are_uppercase_underscore(self, aitoearn_manifest_path):
        """Env-var names must be valid shell identifiers (catalog requires this)."""
        import re

        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        for env_spec in data["auth"]["env"]:
            name = env_spec["name"]
            assert re.match(r"^[A-Z][A-Z0-9_]*$", name), (
                f"env var name {name!r} must be UPPER_SNAKE_CASE"
            )

    def test_no_duplicate_env_var_names(self, aitoearn_manifest_path):
        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        names = [e["name"] for e in data["auth"]["env"]]
        assert len(names) == len(set(names)), f"duplicate env names: {names}"


# ---------------------------------------------------------------------------
# Region switch behavior (what a China user does post-install)
# ---------------------------------------------------------------------------


class TestAitoearnRegionSwitch:
    """Validate the post-install workflow for switching from intl to China."""

    def test_china_url_is_documented_in_post_install(self, aitoearn_manifest_path):
        data = yaml.safe_load(aitoearn_manifest_path.read_text())
        post = data.get("post_install", "").lower()
        assert "aitoearn.cn" in post
        # And it should warn about the 401 if user mixes env + key
        assert "401" in post or "match" in post

    def test_catalog_parser_tolerates_china_url_override(self, catalog_dir, aitoearn_manifest_path):
        """If someone copies the manifest to override the URL to .cn, parser must accept it."""
        import shutil

        # Copy the shipped manifest to the test catalog dir
        target = catalog_dir / "aitoearn-cn-test"
        target.mkdir()
        shutil.copy(aitoearn_manifest_path, target / "manifest.yaml")
        # Override URL
        manifest_file = target / "manifest.yaml"
        data = yaml.safe_load(manifest_file.read_text())
        data["name"] = "aitoearn-cn-test"
        data["transport"]["url"] = "https://aitoearn.cn/api/unified/mcp"
        manifest_file.write_text(yaml.safe_dump(data))

        from hermes_cli.mcp_catalog import _parse_manifest, list_catalog

        entries = list_catalog()
        cn_entry = next(e for e in entries if e.name == "aitoearn-cn-test")
        assert cn_entry.transport.url == "https://aitoearn.cn/api/unified/mcp"
        assert "aitoearn.cn" in cn_entry.transport.url

    def test_sse_fallback_url_in_readme(self):
        """Verify SSE URL is also available — hermes-agent supports SSE transport
        alongside Streamable HTTP, and AiToEarn exposes both.  This is a sanity
        check on our thirdparty-readme archive, not the manifest itself."""
        readme_zh = Path(
            "/home/hermes/thirdparty-readme/aitoearn/readme-zh.md"
        )
        if not readme_zh.is_file():
            pytest.skip("readme-zh.md not yet written")
        content = readme_zh.read_text()
        # SSE endpoint should be documented for users who prefer long-poll
        assert "/api/unified/sse" in content or "SSE" in content


# ---------------------------------------------------------------------------
# Integration with the rest of the catalog
# ---------------------------------------------------------------------------


class TestAitoearnCatalogIntegration:
    """Sanity checks that the shipped entry co-exists with linear and n8n."""

    def test_aitoearn_appears_in_list_catalog(self):
        from hermes_cli.mcp_catalog import list_catalog

        names = {e.name for e in list_catalog()}
        # linear and n8n ship with the repo; aitoearn is the new one we're testing
        assert "aitoearn" in names
        assert "linear" in names
        assert "n8n" in names

    def test_aitoearn_get_entry_returns_parsed(self):
        from hermes_cli.mcp_catalog import get_entry

        e = get_entry("aitoearn")
        assert e is not None
        assert e.name == "aitoearn"
        assert e.transport.type == "http"

    def test_aitoearn_does_not_clash_with_existing_names(self):
        """The name 'aitoearn' must not collide with any other catalog entry."""
        from hermes_cli.mcp_catalog import list_catalog

        names = [e.name for e in list_catalog()]
        assert names.count("aitoearn") == 1


# ---------------------------------------------------------------------------
# Default mcp_servers block (added to ~/.hermes/config.yaml by boss's request)
# ---------------------------------------------------------------------------


class TestAitoearnDefaultConfigBlock:
    """Verify the default block added to ~/.hermes/config.yaml uses the right
    shape (env-var interpolation in headers, env-region selector)."""

    def test_default_block_uses_http_transport(self, tmp_path):
        """The default mcp_servers.aitoearn block is HTTP with x-api-key header."""
        config_path = Path("/home/hermes/.hermes/config.yaml")
        if not config_path.is_file():
            pytest.skip("~/.hermes/config.yaml not present in this test env")
        import yaml

        cfg = yaml.safe_load(config_path.read_text())
        servers = cfg.get("mcp_servers") or {}
        assert "aitoearn" in servers, "aitoearn must be in default mcp_servers"
        block = servers["aitoearn"]
        # transport shape: type=http, url ends in /mcp
        assert block.get("type") in ("http",) or "url" in block
        assert block.get("url", "").endswith("/api/unified/mcp")
        # Auth via headers + env-var interpolation
        headers = block.get("headers") or {}
        assert "x-api-key" in headers, "x-api-key header must be set"
        assert "${AITO_EARN_API_KEY}" in headers["x-api-key"], (
            "API key must be env-var interpolated, not hard-coded"
        )

    def test_default_block_does_not_break_parsing(self):
        """The default block must round-trip through yaml.safe_load."""
        config_path = Path("/home/hermes/.hermes/config.yaml")
        if not config_path.is_file():
            pytest.skip("~/.hermes/config.yaml not present in this test env")
        import yaml

        cfg = yaml.safe_load(config_path.read_text())
        # Re-serialize and re-parse — should not raise
        again = yaml.safe_load(yaml.safe_dump(cfg))
        assert again["mcp_servers"]["aitoearn"]["url"] == cfg["mcp_servers"]["aitoearn"]["url"]
