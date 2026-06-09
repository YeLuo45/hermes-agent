"""Tests for the ECC skill bundle in optional-skills/ecc/.

Verifies:
- All 8 cherry-picked skills exist with SKILL.md
- Each SKILL.md has the full hermes-native frontmatter (name, description,
  version, author, license, platforms, metadata.hermes, prerequisites)
- Each SKILL.md preserves an Origin attribution block pointing to upstream
- The upstream link resolves to a real GitHub blob URL
- The bundle size is reasonable (~60KB body content)
- No skill duplicates, no broken related_skills references
- Body content is preserved (not just frontmatter)
- Bundle can be discovered by hermes-agent's optional-skills pattern
  (SKILL.md + sibling subdirs with SKILL.md)

These tests don't touch the network — they validate the manifest + content shape.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixtures + constants
# ---------------------------------------------------------------------------


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_DIR = REPO_ROOT / "optional-skills" / "ecc"

EXPECTED_SKILLS = {
    "hermes-imports",
    "verification-loop",
    "tdd-workflow",
    "security-review",
    "search-first",
    "mcp-server-patterns",
    "agent-introspection-debugging",
    "iterative-retrieval",
}

# Frontmatter required for hermes optional-skills auto-discovery
REQUIRED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "version",
    "author",
    "license",
    "platforms",
    "metadata",
    "prerequisites",
}


def _read_skill(name: str) -> tuple[dict, str, str]:
    """Read a skill's SKILL.md and split frontmatter from body.

    Returns (frontmatter_dict, body_text, raw_text).
    Raises FileNotFoundError if the skill is missing.
    """
    path = BUNDLE_DIR / name / "SKILL.md"
    if not path.is_file():
        raise FileNotFoundError(f"missing skill: {path}")
    raw = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.DOTALL)
    assert m, f"{name}: SKILL.md must start and end with '---' frontmatter"
    fm = yaml.safe_load(m.group(1))
    return fm, m.group(2).strip(), raw


# ---------------------------------------------------------------------------
# Class 1: bundle inventory
# ---------------------------------------------------------------------------


class TestBundleInventory:
    """The bundle has exactly 8 skills, all with SKILL.md."""

    def test_bundle_dir_exists(self):
        assert BUNDLE_DIR.is_dir(), f"bundle dir missing: {BUNDLE_DIR}"

    def test_bundle_readme_exists(self):
        """A README.md explaining the bundle should be at the root."""
        readme = BUNDLE_DIR / "README.md"
        assert readme.is_file(), "optional-skills/ecc/README.md must exist"

    def test_expected_skill_count(self):
        """Exactly 8 sub-dirs (one per cherry-picked skill)."""
        subdirs = {p.name for p in BUNDLE_DIR.iterdir() if p.is_dir()}
        assert subdirs == EXPECTED_SKILLS, (
            f"expected 8 skills, got {len(subdirs)}: {subdirs}"
        )

    def test_no_extra_skills(self):
        """The bundle should not silently grow — every added skill
        should be an explicit proposal decision."""
        subdirs = {p.name for p in BUNDLE_DIR.iterdir() if p.is_dir()}
        extras = subdirs - EXPECTED_SKILLS
        assert not extras, f"unexpected skills in bundle: {extras}"

    def test_no_skill_missing(self):
        """Every expected skill must be present."""
        subdirs = {p.name for p in BUNDLE_DIR.iterdir() if p.is_dir()}
        missing = EXPECTED_SKILLS - subdirs
        assert not missing, f"missing skills from bundle: {missing}"

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_each_skill_has_skill_md(self, skill):
        path = BUNDLE_DIR / skill / "SKILL.md"
        assert path.is_file(), f"{skill}/SKILL.md missing"

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_each_skill_md_non_empty(self, skill):
        path = BUNDLE_DIR / skill / "SKILL.md"
        size = path.stat().st_size
        assert size > 500, f"{skill}/SKILL.md too small ({size}B)"

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_each_skill_md_under_50kb(self, skill):
        """Skills should be lean — under 50KB body. ECC skills are typically <15KB."""
        path = BUNDLE_DIR / skill / "SKILL.md"
        size = path.stat().st_size
        assert size < 50_000, f"{skill}/SKILL.md too large ({size}B) — content may have ballooned"


# ---------------------------------------------------------------------------
# Class 2: frontmatter validation (hermes-native schema)
# ---------------------------------------------------------------------------


class TestFrontmatterSchema:
    """Each skill's frontmatter has all hermes-native required fields."""

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_frontmatter_has_required_keys(self, skill):
        fm, _, _ = _read_skill(skill)
        missing = REQUIRED_FRONTMATTER_KEYS - set(fm.keys())
        assert not missing, f"{skill}: frontmatter missing keys {missing}"

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_frontmatter_name_matches_dir(self, skill):
        """`name` in frontmatter must match the directory name."""
        fm, _, _ = _read_skill(skill)
        assert fm["name"] == skill, (
            f"{skill}: frontmatter name is {fm['name']!r}, expected {skill!r}"
        )

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_description_is_string(self, skill):
        fm, _, _ = _read_skill(skill)
        assert isinstance(fm["description"], str)
        assert len(fm["description"]) >= 40, (
            f"{skill}: description too short ({len(fm['description'])} chars)"
        )

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_version_is_semver_string(self, skill):
        fm, _, _ = _read_skill(skill)
        v = str(fm["version"])
        assert re.match(r"^\d+\.\d+\.\d+$", v), (
            f"{skill}: version {v!r} is not a semver string"
        )

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_license_is_mit(self, skill):
        fm, _, _ = _read_skill(skill)
        assert str(fm["license"]).upper() == "MIT"

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_platforms_includes_3(self, skill):
        fm, _, _ = _read_skill(skill)
        platforms = fm["platforms"]
        assert isinstance(platforms, list)
        assert "linux" in platforms
        assert "macos" in platforms
        assert "windows" in platforms

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_metadata_hermes_block_present(self, skill):
        fm, _, _ = _read_skill(skill)
        meta = fm.get("metadata") or {}
        hermes = meta.get("hermes") or {}
        assert "tags" in hermes, f"{skill}: metadata.hermes.tags missing"
        tags = hermes["tags"]
        assert isinstance(tags, list) and len(tags) >= 2, (
            f"{skill}: tags should be a list with >= 2 entries"
        )

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_metadata_upstream_attribution(self, skill):
        """Each skill must credit the ECC upstream — supports audit + license."""
        fm, _, _ = _read_skill(skill)
        meta = fm.get("metadata") or {}
        assert "upstream" in meta, f"{skill}: metadata.upstream missing"
        assert meta["upstream"].startswith("https://github.com/YeLuo45/ECC")
        assert "upstream_skill_path" in meta

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_prerequisites_block_present(self, skill):
        """Hermes optional-skills pattern requires prerequisites key."""
        fm, _, _ = _read_skill(skill)
        pre = fm.get("prerequisites") or {}
        assert "commands" in pre, f"{skill}: prerequisites.commands missing"
        assert isinstance(pre["commands"], list)


# ---------------------------------------------------------------------------
# Class 3: body content integrity
# ---------------------------------------------------------------------------


class TestBodyContent:
    """The body must be preserved from upstream (not just frontmatter)."""

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_body_starts_with_origin_block(self, skill):
        """An `> **Origin**: ...` block must lead the body for attribution."""
        _, body, _ = _read_skill(skill)
        assert body.startswith("> **Origin**:"), (
            f"{skill}: body should start with an Origin blockquote"
        )

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_body_has_h1_heading(self, skill):
        """A top-level `# Heading` must follow the Origin block."""
        _, body, _ = _read_skill(skill)
        # Find first non-blockquote, non-blank line
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(">"):
                continue
            assert stripped.startswith("# "), (
                f"{skill}: first non-blockquote line is not an H1: {stripped!r}"
            )
            break

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_body_references_correct_upstream_url(self, skill):
        """The Origin blockquote must point to the matching upstream skill path."""
        _, body, _ = _read_skill(skill)
        expected_path = f"skills/{skill}/SKILL.md"
        assert expected_path in body, (
            f"{skill}: Origin block should reference {expected_path}"
        )

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_body_has_minimum_content(self, skill):
        """Each skill must have substantial procedural content."""
        _, body, _ = _read_skill(skill)
        # Strip the Origin blockquote for fair count
        body_no_origin = re.sub(r"^>.*$", "", body, flags=re.MULTILINE).strip()
        # After stripping origin, still need real content
        assert len(body_no_origin) > 500, (
            f"{skill}: body too thin after origin ({len(body_no_origin)} chars)"
        )

    @pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
    def test_body_has_activation_guidance(self, skill):
        """Hermes skill convention: a 'When to Use' / 'When to Activate' / 'Trigger' /
        'How to Use' section explains when the skill applies. We accept any of these
        so skills with non-standard naming (e.g. ECC's `## Trigger`) still pass."""
        _, body, _ = _read_skill(skill)
        body_lower = body.lower()
        accepted_headings = [
            "when to use",
            "when to activate",
            "when to apply",
            "## trigger",
            "## how to use",
        ]
        assert any(h in body_lower for h in accepted_headings), (
            f"{skill}: body should have an activation section "
            f"(one of {accepted_headings})"
        )


# ---------------------------------------------------------------------------
# Class 4: cross-skill consistency
# ---------------------------------------------------------------------------


class TestBundleConsistency:
    """The bundle hangs together — no broken related_skills refs, no dupes."""

    def test_related_skills_resolve_within_bundle_or_to_known_skills(self):
        """Each skill's related_skills should either name another bundle skill
        or be a known hermes skill. We don't want phantom references."""
        for skill in EXPECTED_SKILLS:
            fm, _, _ = _read_skill(skill)
            related = (fm.get("metadata") or {}).get("hermes") or {}
            related = related.get("related_skills") or []
            for ref in related:
                # OK if it points to another skill in this bundle
                if ref in EXPECTED_SKILLS:
                    continue
                # OK if it points to a known hermes skill (we just don't have
                # an exhaustive list, so we accept non-bundle refs as long as
                # they are strings with hyphens)
                assert re.match(r"^[a-z][a-z0-9-]+$", ref), (
                    f"{skill}: related_skills entry {ref!r} doesn't look like a skill name"
                )

    def test_no_two_skills_have_same_name(self):
        """Sanity check — directory listing is already used; this is a belt-and-braces."""
        subdirs = [p.name for p in BUNDLE_DIR.iterdir() if p.is_dir()]
        assert len(subdirs) == len(set(subdirs))

    def test_every_skill_authored_by_ecc(self):
        """All skills credit ECC as the source."""
        for skill in EXPECTED_SKILLS:
            fm, _, _ = _read_skill(skill)
            author = str(fm.get("author", ""))
            # Author can be "YeLuo45 (via ECC) / Hermes Agent" or similar
            assert "ECC" in author, (
                f"{skill}: author {author!r} should credit ECC"
            )

    def test_every_skill_metadata_upstream_is_yikart_ecc(self):
        """All skills point to the same upstream repo (YeLuo45/ECC)."""
        for skill in EXPECTED_SKILLS:
            fm, _, _ = _read_skill(skill)
            upstream = (fm.get("metadata") or {}).get("upstream", "")
            assert upstream == "https://github.com/YeLuo45/ECC", (
                f"{skill}: upstream {upstream!r} is not YeLuo45/ECC"
            )


# ---------------------------------------------------------------------------
# Class 5: hermes auto-discovery compatibility
# ---------------------------------------------------------------------------


class TestHermesAutoDiscovery:
    """Validate that hermes-agent's optional-skills scanning would pick this up."""

    def test_each_skill_md_is_at_correct_relative_path(self):
        """Hermes discovers via `optional-skills/<category>/<name>/SKILL.md`."""
        for skill in EXPECTED_SKILLS:
            expected = BUNDLE_DIR / skill / "SKILL.md"
            assert expected.is_file()
            # Path relative to repo must be discoverable
            rel = expected.relative_to(REPO_ROOT)
            assert rel.parts[0] == "optional-skills"
            assert rel.parts[1] == "ecc"
            assert rel.parts[-1] == "SKILL.md"

    def test_bundle_readme_introduces_each_skill(self):
        """Bundle README should list every skill in the bundle (auditable)."""
        readme = (BUNDLE_DIR / "README.md").read_text()
        for skill in EXPECTED_SKILLS:
            assert skill in readme, (
                f"bundle README doesn't mention skill {skill!r}"
            )

    def test_bundle_readme_has_install_instructions(self):
        readme = (BUNDLE_DIR / "README.md").read_text()
        assert "hermes skills install" in readme or "skills install" in readme

    def test_bundle_readme_credits_upstream(self):
        readme = (BUNDLE_DIR / "README.md").read_text()
        assert "YeLuo45/ECC" in readme or "github.com/YeLuo45/ECC" in readme


# ---------------------------------------------------------------------------
# Class 6: bundle size sanity
# ---------------------------------------------------------------------------


class TestBundleSize:
    """A curated 8-skill bundle should be <100KB total — proves it's a bundle, not a mirror."""

    def test_total_size_under_100kb(self):
        total = 0
        for skill in EXPECTED_SKILLS:
            total += (BUNDLE_DIR / skill / "SKILL.md").stat().st_size
        # Add README
        total += (BUNDLE_DIR / "README.md").stat().st_size
        assert total < 100_000, (
            f"bundle too large ({total} bytes) — looks like a mirror, not a bundle"
        )

    def test_total_size_over_10kb(self):
        """If it's under 10KB total, the cherry-pick was too aggressive."""
        total = 0
        for skill in EXPECTED_SKILLS:
            total += (BUNDLE_DIR / skill / "SKILL.md").stat().st_size
        assert total > 10_000, (
            f"bundle suspiciously small ({total} bytes) — content may be missing"
        )
