# Optional Skills

Official skills maintained by Nous Research that are **not activated by default**.

These skills ship with the hermes-agent repository but are not copied to
`~/.hermes/skills/` during setup. They are discoverable via the Skills Hub:

```bash
hermes skills browse               # browse all skills, official shown first
hermes skills browse --source official  # browse only official optional skills
hermes skills search <query>       # finds optional skills labeled "official"
hermes skills install <identifier> # copies to ~/.hermes/skills/ and activates
```

## Why optional?

Some skills are useful but not broadly needed by every user:

- **Niche integrations** — specific paid services, specialized tools
- **Experimental features** — promising but not yet proven
- **Heavyweight dependencies** — require significant setup (API keys, installs)

By keeping them optional, we keep the default skill set lean while still
providing curated, tested, official skills for users who want them.

## Curated bundles

Some optional-skill directories are **bundles** — curated subsets of a larger
upstream project, cherry-picked for Hermes operators. Bundles are listed with
the same `official` source label so `hermes skills browse --source official`
picks them up, and each sub-skill is independently installable.

| Bundle | Source | Skills | Why a bundle |
|---|---|---|---|
| [`ecc/`](ecc/README.md) | [YeLuo45/ECC](https://github.com/YeLuo45/ECC) | 8 (verification-loop, tdd-workflow, security-review, search-first, hermes-imports, mcp-server-patterns, agent-introspection-debugging, iterative-retrieval) | ECC ships 200+ skills and 4,000 files; bundle keeps the universal top 8 (~60KB) |

For the full ECC suite (~35 MB), clone the upstream repo and use the
`hermes-imports` skill (or the [HERMES-OPENCLAW-MIGRATION guide](https://github.com/YeLuo45/ECC/blob/main/docs/HERMES-OPENCLAW-MIGRATION.md))
to bring in additional skills as needed.
