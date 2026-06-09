# CSV Structure Corruption: Recovery Playbook

## What Happened (2026-05-16)

`projects.csv` had its schema destroyed — reduced from 8 fields to 4 fields:
- **Expected**: `id,name,proposal_count,git_repo,local_path,prj_url,description,last_update`
- **Actual**: `id,name,proposal_count,git_repo`

**Root cause**: CSV was modified directly (e.g., via `execute_code` or `patch` tool) without going through `proposal_manager_cli.py`, which maintains field consistency.

**This violated Rule 1 in the skill**:
> All changes MUST go through `proposal_manager_cli.py`

## Recovery Steps

### Step 1: Identify the problem
```bash
head -1 /home/hermes/proposals/projects.csv
# Expected: id,name,proposal_count,git_repo,local_path,prj_url,description,last_update
# If you see fewer fields, structure is corrupted
```

### Step 2: Restore from backup
```bash
# Find the most recent good backup
ls -t /home/hermes/proposals/backups/

# Check backup structure before restoring
head -1 /home/hermes/proposals/backups/backup_YYYYMMDD_HHMMSS/projects.csv

# Restore (manual copy — backup dirs, not tar.gz)
 cp /home/hermes/proposals/backups/backup_YYYYMMDD_HHMMSS/projects.csv \
    /home/hermes/proposals/projects.csv
```

### Step 3: Re-derive missing fields
If `prj_url` was lost but `git_repo` exists, re-infer:
```python
import csv, re

with open('projects.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

for row in rows:
    git_repo = row.get('git_repo', '')
    m = re.match(r'https://github\.com/YeLuo45/([^/]+)', git_repo)
    if m and not row.get('prj_url'):
        row['prj_url'] = f'https://yeluo45.github.io/{m.group(1)}/'

fieldnames = ['id','name','proposal_count','git_repo','local_path','prj_url','description','last_update']
with open('projects.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
```

### Step 4: Push restored data to GitHub
```python
# Generate proposals.json locally
import csv, json, re

with open('projects.csv', 'r') as f:
    projects = list(csv.DictReader(f))

website_projects = []
for p in projects:
    repo = p.get('git_repo','')
    m = re.match(r'https://github\.com/YeLuo45/([^/]+)', repo)
    github_pages = f'https://yeluo45.github.io/{m.group(1)}/' if m else ''
    website_projects.append({
        'id': p['id'], 'name': p['name'],
        'gitRepo': repo, 'githubPages': github_pages,
        'prjUrl': p.get('prj_url','') or github_pages,
        'url': p.get('prj_url','') or github_pages,
        'localPath': p.get('local_path',''),
        'description': p.get('description',''),
        'proposalCount': int(p.get('proposal_count','0') or '0'),
        'lastUpdate': p.get('last_update',''),
        'proposals': []
    })

with open('/tmp/proposals.json', 'w') as f:
    json.dump({'version':3, 'projects': website_projects}, f, ensure_ascii=False, indent=2)

# Upload via REST API (avoids git push network issues)
import urllib.request, json, base64, subprocess
GH_TOKEN = subprocess.check_output(['gh', 'auth', 'token']).decode().strip()
req = urllib.request.Request(
    'https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json?ref=gh-pages',
    headers={'Authorization': f'Bearer {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
)
with urllib.request.urlopen(req, timeout=20) as r:
    SHA = json.loads(r.read())['sha']
with open('/tmp/proposals.json', 'rb') as f:
    content = base64.b64encode(f.read()).decode()
payload = json.dumps({'message': 'restore: projects.csv 8-field structure', 'content': content, 'sha': SHA}).encode()
req = urllib.request.Request(
    'https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json?ref=gh-pages',
    data=payload, headers={'Authorization': f'Bearer {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}, method='PUT'
)
with urllib.request.urlopen(req, timeout=30) as r:
    result = json.loads(r.read())
    print('SUCCESS' if 'commit' in result else result)
```

## Prevention: NEVER do these

| WRONG | Correct |
|----------|-----------|
| `execute_code` writes to CSV directly | Use `proposal_manager_cli.py` for all CSV changes |
| `patch` tool rewrites entire CSV | Use `proposal_manager_cli.py proposal update ...` |
| Manually add/remove CSV columns | Schema is fixed; field order matters |
| `proposals.csv` with duplicate columns | Always deduplicate when rewriting CSVs |

## The One Safe Exception

The ONLY time you may write CSV directly is when recovering from corruption, and even then:
1. Restore from backup first
2. Re-derive missing fields via script
3. Verify field count matches schema exactly
4. Push restored data to GitHub immediately

## CSV Schema (authoritative)

```
projects.csv:    id,name,proposal_count,git_repo,local_path,prj_url,description,last_update
proposals.csv:   id,title,owner,status,project_id,project_name,stage,prd_path,tech_solution_path,
                 project_path,git_repo,prj_url,deployment_branch,prd_confirmation,tech_expectations,
                 acceptance,research_direction,last_update,engine,target,game_type,notes
mapping.csv:     project_id,project_name,proposal_id,
                 proposal_name
```
