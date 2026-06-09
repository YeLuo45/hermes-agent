# ECC Skill Bundle (Optional)

A curated subset of skills from the [Everything Claude Code](https://github.com/YeLuo45/ECC) (ECC) project, the
harness-native operator system by YeLuo45. ECC ships **200+ skills** spanning 12+ language
ecosystems; this bundle cherry-picks the **8 most universally useful** for Hermes operators.

## Why a curated subset

ECC is large (~4,000 files, ~35 MB) and opinionated — most of its skills target specific
harnesses (Codex, Cursor, OpenCode, Kiro, ...) or niche domains (defi-amm-security,
healthcare-phi-compliance, etc.). For the average Hermes operator, the 8 skills below cover
the highest-leverage patterns:

- **TDD / verification** — write tests first, verify before shipping
- **Security** — threat model before merging
- **Research-first** — search before implementing
- **Hermes-specific** — hermes-imports, mcp-server-patterns, agent-introspection-debugging
- **RAG** — iterative-retrieval for codebase question-answering

For the full ECC suite, see [github.com/YeLuo45/ECC](https://github.com/YeLuo45/ECC) — it
targets Claude Code, Codex, Cursor, OpenCode, Kiro, Gemini, Zed, and other harnesses.

## Skills in this bundle

| Skill | Domain | Hermes-tag | When to use |
|---|---|---|---|
| [`hermes-imports`](./hermes-imports/SKILL.md) | migration | hermes, ecc, migration | Sanitize a local Hermes workflow into a public ECC skill |
| [`verification-loop`](./verification-loop/SKILL.md) | quality | verification, tdd, quality-gate | After every non-trivial change — run typecheck/lint/tests/build before declaring done |
| [`tdd-workflow`](./tdd-workflow/SKILL.md) | testing | tdd, testing, red-green-refactor | Adding a feature or fixing a bug — red/green/refactor with discipline |
| [`security-review`](./security-review/SKILL.md) | security | security, owasp, threat-model | Touching auth, payments, user data, or external APIs — threat model + checklist |
| [`search-first`](./search-first/SKILL.md) | research | research, documentation | Non-trivial implementation choice — search official docs/RFCs/issues first |
| [`mcp-server-patterns`](./mcp-server-patterns/SKILL.md) | mcp | mcp, typescript, server | Building a new MCP server (TypeScript SDK) — tools/resources/prompts/transport |
| [`agent-introspection-debugging`](./agent-introspection-debugging/SKILL.md) | agent | debugging, agent, self-repair | Agent run is failing repeatedly, looping, or drifting — diagnose before retrying |
| [`iterative-retrieval`](./iterative-retrieval/SKILL.md) | rag | rag, retrieval, research | Question answering over large codebases — query/re-rank/augment loop |

## Origin and licensing

All body content is preserved **verbatim** from upstream
[YeLuo45/ECC](https://github.com/YeLuo45/ECC/blob/main/skills/<name>/SKILL.md) (branch `main`).
Only the YAML frontmatter was enriched to match Hermes's `optional-skills/` schema
(added `version`, `author`, `license`, `platforms`, `metadata.hermes`).

Upstream license: **MIT** (per the ECC project). When cherry-picked into Hermes
`optional-skills/`, the license stays MIT; users may modify or re-distribute under the
same terms.

## Install

```bash
# Browse the bundle
hermes skills browse --source official | grep '^ecc/'

# Install a specific skill
hermes skills install ecc/verification-loop
hermes skills install ecc/tdd-workflow

# Install the whole bundle
hermes skills install ecc/hermes-imports ecc/verification-loop ecc/tdd-workflow \
                    ecc/security-review ecc/search-first ecc/mcp-server-patterns \
                    ecc/agent-introspection-debugging ecc/iterative-retrieval
```

Once installed, the skill is copied to `~/.hermes/skills/` and activated. Use
`--skill <name>` to inject it into a session, or set up automatic discovery via
`~/.hermes/config.yaml`.

## Verifying the bundle

```bash
ls optional-skills/ecc/                                  # 8 sub-dirs
for d in optional-skills/ecc/*/; do
  head -1 "$d/SKILL.md"                                  # must start with "---"
done
```

## Updating from upstream

This bundle pins the **main branch** at integration time. To refresh from upstream:

```bash
./scripts/sync-ecc-bundle.sh   # (TBD — see proposal P-20260607-006)
```

For now, manual refresh:

```bash
for s in hermes-imports verification-loop tdd-workflow security-review search-first \
         mcp-server-patterns agent-introspection-debugging iterative-retrieval; do
  curl -sL https://raw.githubusercontent.com/YeLuo45/ECC/main/skills/$s/SKILL.md \
    > /tmp/$s.md
done
# Then re-run the cherry-pick script (see proposal)
```

## Related

- Proposal: `/home/hermes/proposals/P-20260607-006.md`
- Tests: `/home/hermes/.hermes/hermes-agent/tests/optional_skills/test_ecc_bundle.py`
- Upstream: https://github.com/YeLuo45/ECC
- Hermes optional-skills convention: `optional-skills/DESCRIPTION.md`
