# proposals.csv Schema Change Log

## Current Structure (2026-05-16+)

```
id,title,owner,status,project_id,project_name,stage,prd_path,tech_solution_path,project_path,deployment_branch,prd_confirmation,tech_expectations,acceptance,research_direction,last_update,engine,target,game_type,notes
```

**20 fields** — git_repo and prj_url removed (冗余字段，已在projects.csv中存在).

## Historical Structure (pre-2026-05-16)

```
id,title,owner,status,project_id,project_name,stage,prd_path,tech_solution_path,project_path,git_repo,prj_url,deployment_branch,prd_confirmation,tech_expectations,acceptance,research_direction,last_update,engine,target,game_type,notes
```

**22 fields** — 两字段被移除:
- `git_repo` —冗余，projects.csv 中已有
- `prj_url` —冗余，projects.csv 中已有

## Scripts That Must Be Updated on Schema Change

| File | What to Update |
|------|----------------|
| `SKILL.md` | proposals.csv section header + field list + sample row |
| `SKILL-zh.md` | proposals.csv section header + field list + sample row |
| `scripts/sync-proposals-to-website.py` | Docstring comment at top |
| `references/csv-structure-recovery.md` | Structure reference |

## Data Migration Command

```python
import csv

old_csv = "/path/to/proposals.csv"
backup = old_csv + ".bak_before_field_removal"

with open(old_csv, 'r', encoding='utf-8') as f:
    content = f.read()
with open(backup, 'w', encoding='utf-8') as f:
    f.write(content)

NEW_HEADERS = ['id','title','owner','status','project_id','project_name','stage','prd_path',
               'tech_solution_path','project_path','deployment_branch','prd_confirmation',
               'tech_expectations','acceptance','research_direction','last_update',
               'engine','target','game_type','notes']

with open(old_csv, 'r', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

with open(old_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=NEW_HEADERS, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
```

## Verification

```bash
# Check field count
head -1 old.csv | tr ',' '\n' | wc -l   # before: 22
head -1 new.csv | tr ',' '\n' | wc -l   # after: 20

# Check row count unchanged
wc -l old.csv new.csv   # counts must match
```