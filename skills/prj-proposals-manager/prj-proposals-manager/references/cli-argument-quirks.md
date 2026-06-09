# proposal_manager_cli.py CLI Argument Quirks

## project add

```bash
# ❌ ERROR: git_repo format rejected
python3 .../proposal_manager_cli.py project add \
  --name "pixel-pal-web" \
  --git-repo "YeLuo45/pixel-pal-web"
# ERROR: git_repo 格式错误: YeLuo45/pixel-pal-web，需以 http:// https:// 或 git@ 开头

# ✅ 正确：必须 https:// 开头
python3 .../proposal_manager_cli.py project add \
  --name "pixel-pal-web" \
  --git-repo "https://github.com/YeLuo45/pixel-pal-web"
# 自动生成项目ID: PRJ-20260519-001
```

**Note**: `--name` is required. `--git-repo` is required but must be full URL format.

## project next-id

```bash
# 自动生成下一个项目ID
python3 .../proposal_manager_cli.py project next-id
```

## proposal add

```bash
# ❌ ERROR: --id is NOT supported for proposal add (ID is auto-generated)
python3 .../proposal_manager_cli.py proposal add \
  --id P-20260519-003 \
  --title "..."

# ✅ 正确：自动分配ID，或用 --title + --project-id
python3 .../proposal_manager_cli.py proposal add \
  --title "pixel-pal-web 完全移除MUI依赖" \
  --project-id PRJ-20260519-001 \
  --owner "小墨"
```

## proposal update

```bash
# ❌ ERROR: --id is NOT supported, uses positional arg
python3 .../proposal_manager_cli.py proposal update \
  --id P-20260519-003 \
  --notes "..."
# error: unrecognized arguments: --id

# ✅ 正确：proposal ID is positional
python3 .../proposal_manager_cli.py proposal update P-20260519-003 \
  --notes "Phase 1 完成：基础设施+6个基础组件。Commit: 2b3bfd8。"
```

**Note**: `--stage` value must be from the valid enum; invalid values cause errors.

## proposal list

```bash
# 查看所有提案
python3 .../proposal_manager_cli.py proposal list

# 指定字段
python3 .../proposal_manager_cli.py proposal list --fields id,title,status,project_name
```

## All positional-arg commands

| Command | Positional Arg |
|---------|---------------|
| `proposal update <id>` | proposal ID |
| `project update <id>` | project ID |
| `proposal list` | none |
| `project list` | none |
| `proposal add` | none (uses flags) |

## Direct CSV manipulation (fallback)

When CLI gives unexpected errors, manipulate CSV directly:

```python
import csv
rows = []
with open('~/.hermes/proposals/proposals.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['id'] == 'P-20260519-003':
            row['notes'] = 'Updated note'
            row['last_update'] = '2026-05-19'
        rows.append(row)
with open('~/.hermes/proposals/proposals.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
```

**Always verify row count after direct CSV manipulation:**
```bash
wc -l ~/.hermes/proposals/proposals.csv
```
