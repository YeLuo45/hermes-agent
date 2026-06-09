## projects.csv Data Quality Reference

## Standard Structure (8 fields)

## prjId Format Enforcement

Every project `id` MUST follow the `PRJ-YYYYMMDD-NNN` format (e.g., `PRJ-20260516-001`).
Non-compliant IDs (bare repo names like `hermes-agent-design`, `cultivation-simulator`) MUST be renumbered
to the next available sequence on the correction date.

**Correction process (2026-05-16 example — fixed 3 non-compliant IDs):**

1. Find max PRJ-YYYYMMDD-* number for the correction date → `PRJ-20260515-013`
2. Assign sequentially: `PRJ-20260516-001`, `-002`, `-003`, etc.
3. Update projects.csv `id` field for each non-compliant entry
4. Update proposals.csv `project_id` field for all referencing proposals (e.g., P-20260512-003, P-20260513-003)
5. Regenerate proposals.json locally: read both CSV → write JSON
6. Push via sync script: `GITHUB_TOKEN=$(gh auth token) python3 scripts/sync-proposals-to-website.py`

**CRITICAL:** After any manual CSV edit, always regenerate proposals.json and re-push.
Do NOT rely on partial updates — the CSV and JSON must stay in sync.

## Standard Structure (8 fields)
```
id,name,proposal_count,git_repo,local_path,prj_url,description,last_update
```

## Common Data Quality Issues

### 1. local_path contains URL instead of filesystem path
Historical entries mistakenly populate `local_path` with `https://yeluo45.github.io/{repo}`.
This field should be empty or a local path. The correct field for GitHub Pages URLs is `prj_url`.

### 2. git_repo has `.git` suffix
Example: `https://github.com/YeLuo45/calculator-app.git`
Must strip `.git` before inferring `prj_url`.

### 3. Non-YeLuo45 git_repo owners
Some entries reference third-party repos (e.g., `Sonic-Yoda/AstrBot`).
For projects under `YeLuo45/*` umbrella, redirect to `YeLuo45/{repo}`.

### 4. Duplicate/missing columns from improper CSV rewriting
If CSV shows only 4 fields instead of 8, a prior rewrite lost columns.
Recovery: restore from backup, then re-infer `prj_url` via regex from `git_repo`.

### 5. prj_url inferred with `.git` suffix left in repo name
**Real case (2026-05-21)**: `plants-vs-zombies` git_repo was `https://github.com/YeLuo45/plants-vs-zombies.git`
(note the `.git` suffix). The regex extracted repo name incorrectly, producing prj_url
`https://yeluo45.github.io/plants-vs-zombies-temp/` instead of `plants-vs-zombies/`.

**Fix**: Always strip `.git` suffix from repo name before inference:
```python
repo = m.group(1).rstrip('/').removesuffix('.git')
```

### 6. CSV `name` field doesn't match filesystem directory name
Some projects have CSV `name` that differs from the actual directory name:
- `AstrBot` (CSV) vs `AstrBot` (filesystem) — OK
- `openspec` (CSV after rename from `openspec-design`) vs `OpenSpec` (filesystem)
- `OpenMAIC` (CSV) vs `OpenMAIC` (filesystem)

When migrating directories, ALWAYS `ls` the source to get the exact directory name.
Do NOT assume `CSV['name']` == `os.path.basename(local_path)`.

## prj_url Inference Rule
```python
import re
m = re.match(r'https://github\.com/YeLuo45/([^/]+)', git_repo)
if m:
    repo = m.group(1).rstrip('/').removesuffix('.git')  # strip .git
    prj_url = f'https://yeluo45.github.io/{repo}/'
```

## Projects That Don't Exist on GitHub (as of 2026-05-16)
- `room-escape-puzzle` — 404, repo may be deleted or renamed
- `todo-list` — repo is `todolist` not `todo-list`

## Projects with No GitHub Pages Deployment (pre-2026-05-16 status)
These repos existed but had no Pages enabled as of 2026-05-15. As of 2026-05-16, Pages were
enabled for: android-hello, todo-app, personalClaw, OpenMAIC, tower-baby-guard, harness-desktop,
open-space-design, scrapling-design, claude-code-design, claudecodesrc-design, freqtrade-develop-design,
langcli-design, ohmypi-design, opencode-dev-design. Verify current status via GitHub API.

## Design Projects
Projects with `-design` suffix are documentation/repo-analysis projects, not deployed apps.
Their `prj_url` will 404 — this is expected. They track design docs, not running deployments.