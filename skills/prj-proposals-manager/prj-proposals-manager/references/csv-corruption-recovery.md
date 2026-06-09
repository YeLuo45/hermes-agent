# proposals.csv / projects.csv Corruption Recovery

## Symptoms
- Website shows far fewer projects than `proposal-index.md` has
- `wc -l proposals.csv` or `projects.csv` returns suspiciously low count
- Sync script reports success but website data is incomplete

## Diagnosis: CSV Row Count Baseline

```bash
# Check current vs expected counts
wc -l ~/.hermes/proposals/projects.csv   # Should be ~69 (header + 68 projects)
wc -l ~/.hermes/proposals/proposals.csv  # Should be ~220+ (header + proposals)

# Check backup counts (pick most recent good backup)
wc -l ~/.hermes/proposals/backups/backup_YYYYMMDD_HHMMSS/projects.csv
wc -l ~/.hermes/proposals/backups/backup_YYYYMMDD_HHMMSS/proposals.csv
```

## Recovery Procedure

### Step 1: Identify which CSV is corrupted
| Symptom | Corrupted File |
|---------|---------------|
| projects.csv row count << expected | projects.csv |
| proposals.csv row count << expected | proposals.csv |
| proposals.csv OK but website shows 0 proposals per project | proposals.csv (check project_name join) |

### Step 2: Restore from Backup
```bash
# Always backup current before overwriting
cp ~/.hermes/proposals/projects.csv ~/.hermes/proposals/projects.csv.broken
cp ~/.hermes/proposals/proposals.csv ~/.hermes/proposals/proposals.csv.broken

# Restore from most recent good backup
cp ~/.hermes/proposals/backups/backup_YYYYMMDD_HHMMSS/projects.csv \
   ~/.hermes/proposals/projects.csv

cp ~/.hermes/proposals/backups/backup_YYYYMMDD_HHMMSS/proposals.csv \
   ~/.hermes/proposals/proposals.csv

# Verify restored counts
wc -l ~/.hermes/proposals/projects.csv
wc -l ~/.hermes/proposals/proposals.csv
```

### Step 3: Re-push CSV to GitHub via REST API
```bash
export GITHUB_TOKEN=$(gh auth token)
cd /home/hermes/.hermes/proposals

# Push via REST API (git push may be blocked)
python3 scripts/sync-proposals-to-website.py --csv-only
```

If script fails, push manually via REST API — use FULL 40-char SHAs, not truncated (truncated SHAs cause 422 errors).

### Step 4: Regenerate and push proposals.json
```python
# Generate from restored CSV (match by project_name → name)
# IMPORTANT: proposals.csv uses 'project_name' (not 'project_id') to join projects
```

### Step 5: Verify
```bash
git ls-remote https://github.com/YeLuo45/prj-proposals-manager.git master
curl -s https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/<commit>/data/proposals.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{len(d['projects'])} projects\")"
```

## Root Causes Seen

1. **Accidental overwrite** — A sync or edit operation wrote only a subset of rows
2. **execute_code write corruption** — Python DictWriter can silently drop fields not in fieldnames list
3. **Deduplication bug** — Deduplicating by `id` alone (not `(id, project_name)`) deletes cross-project duplicates

## Prevention
- After any CSV write, immediately `wc -l` to verify row count
- Backup before any manual CSV edit
- Deduplication must use composite key `(id, project_name)`
