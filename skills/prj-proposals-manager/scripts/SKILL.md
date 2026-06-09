---
name: prj-proposals-manager-scripts
description: prj-proposals-manager 技能中所有脚本的内联引用 — Data CLI、GitHub API、Git 部署、Cron 定时任务、CSV 修复脚本
---

# Scripts — prj-proposals-manager

## 1. Data Management CLI

**所有项目和提案的增删改必须通过 CLI 进行，禁止直接写入 CSV。**

```bash
python3 /home/hermes/.hermes/skills/prj-proposals-manager/scripts/proposal_manager_cli.py <command> [options]
```

### 项目管理

```bash
# 新增项目（自动生成ID）
python3 scripts/proposal_manager_cli.py project add --name "项目名" --git-repo "https://github.com/owner/repo"

# 列出项目
python3 scripts/proposal_manager_cli.py project list --fields id,name,proposal_count

# 获取单个项目
python3 scripts/proposal_manager_cli.py project get PRJ-20260417-001 --json

# 更新项目
python3 scripts/proposal_manager_cli.py project update PRJ-20260417-001 --name "新名称"

# 删除项目（需确认无活跃提案，或用 --force 强制）
python3 scripts/proposal_manager_cli.py project delete PRJ-20260513-001 --force
```

### 提案管理

```bash
# 新增提案（自动生成ID）
python3 scripts/proposal_manager_cli.py proposal add --title "提案标题" --project-id PRJ-20260417-001

# 列出提案（支持过滤）
python3 scripts/proposal_manager_cli.py proposal list --fields id,title,status,project_name
python3 scripts/proposal_manager_cli.py proposal list --status active
python3 scripts/proposal_manager_cli.py proposal list --project-id PRJ-20260417-001

# 获取单个提案
python3 scripts/proposal_manager_cli.py proposal get P-20260513-001 --json

# 更新提案
python3 scripts/proposal_manager_cli.py proposal update P-20260513-001 --status "in_dev"
python3 scripts/proposal_manager_cli.py proposal update P-20260513-001 --status "accepted" --acceptance "accepted"

# 删除提案（软删除，直接移除）
python3 scripts/proposal_manager_cli.py proposal delete P-20260513-001

# 归档提案（软删除，标记为 archived）
python3 scripts/proposal_manager_cli.py proposal archive P-20260513-001
```

## 2. Init Script

首次使用或目录损坏时：

```bash
python3 /home/hermes/.hermes/skills/prj-proposals-manager/scripts/init_proposals_dir.py
```

**检测逻辑**：根目录不存在→自动初始化；子目录/文件缺失→补建；CSV为空→重建；CSV已有数据（>1行）→拒绝初始化。

## 3. GitHub API Scripts

**Token**: `ghp_XXXXX`（YeLuo45），或从 `~/.hermes/tools/github-token.txt` 读取

### GET proposals.json SHA

```python
import urllib.request, json

TOKEN = open('/home/hermes/.hermes/tools/github-token.txt').read().strip()
REPO = 'YeLuo45/prj-proposals-manager'
DATA_PATH = 'data/proposals.json'

url = f'https://api.github.com/repos/{REPO}/contents/{DATA_PATH}'
req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    sha = data['sha']
    content = base64.b64decode(data['content']).decode('utf-8')
```

### PUT proposals.json

```python
import urllib.request, json, base64

sha = get_sha(DATA_PATH)  # 见上
url = f'https://api.github.com/repos/{REPO}/contents/{DATA_PATH}'
data_put = json.dumps({
    'message': 'feat: add P-YYYYMMDD-XXX <name>',
    'content': base64.b64encode(json.dumps(new_data, ensure_ascii=False).encode()).decode(),
    'sha': sha
})
req = urllib.request.Request(url, data=data_put.encode(),
    headers={'Authorization': f'token {TOKEN}', 'Content-Type': 'application/json'}, method='PUT')
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read()).get('commit', {}).get('sha', '?')[:8])
```

### PATCH repo description

```python
PATCH https://api.github.com/repos/YeLuo45/<repo>
body: { "description": "<Chinese>", "homepage": "<pages-url>" }
```

## 4. Website CSV 校验与修复

**Website 枚举（与内部状态不同）**: status=`active`/`in_dev`/`archived`, type=`web`/`app`/`package`

**内部→网站映射**: `delivered`/`deployed`/`accepted`→`active`, `approved_for_dev`/`intake`/`in_dev`→`in_dev`

```python
import csv, re

# 读取
with open('proposals.csv', 'r') as f:
    rows = list(csv.DictReader(f))

# 修复 status
status_map = {'delivered': 'active', 'deployed': 'active', 'accepted': 'active',
              'approved_for_dev': 'in_dev', 'intake': 'in_dev'}
for row in rows:
    if row['status'] in status_map:
        row['status'] = status_map[row['status']]

# 修复 last_update（从 P-ID 推导）
for row in rows:
    if not row.get('last_update') or row['last_update'] in ('', 'undefined'):
        pid = row['id']
        date_str = pid.split('-')[1]
        row['last_update'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

# 去重（保留第一条）
seen = set()
deduped = [row for row in rows if row['id'] not in seen and not seen.add(row['id'])]

# 写回
with open('proposals.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(deduped)
```

## 5. Git Deployment

```bash
# 创建部署分支
cd ${DEV_OUTPUT_DIR}/<项目名>/proposals
git checkout -b deploy/<项目名>-<YYYYMMDD>

# 提交
git add .
git commit -m "deploy: <项目名> P-YYYYMMDD-XXX"
git push -u origin deploy/<项目名>-<YYYYMMDD>
```

## 6. Cron 倒计时

### PRD 确认 / 技术诉求 / 研究方向（通用模板）

```python
cron(action='create',
     schedule='YYYY-MM-DDTHH:MM:SS+08:00',  # now + 5min
     prompt='【倒计时到期】提案 P-YYYYMMDD-XXX <类型>确认超时，默认通过处理。请将 <类型> 更新为 timeout-approved 并继续下一阶段。',
     name='P-YYYYMMDD-XXX-<type>-confirm')
```

## 7. Hermes-agent Sync

```bash
cd /home/hermes/.hermes
git checkout -b feature/hermes$(date +%y%m%d)
git add proposals/
git commit -m "sync: update proposals from hermes-agent $(date +%Y-%m-%d)"
git push -u https://YeLuo45:***@github.com/YeLuo45/hermes-agent.git feature/hermes$(date +%y%m%d)
```

## 8. CSV Sync from GitHub

```bash
GITHUB_TOKEN=$GITHUB_TOKEN \
  python3 ~/.hermes/scripts/sync-proposals-to-website.py --csv-only
```

**数据流向（以本地为准）**：
```
本地 proposal-index.md 有提案？
  → YES: 本地数据为 source of truth，构建项目结构推送到 GitHub
  → NO:  以 GitHub 现有 data/proposals.json 为 fallback
       ↓
推送后从 GitHub 拉取完整数据 → 生成 CSV 到本地
```

## 9. Proposal ID Query

```bash
grep "P-$(date +%Y%m%d)" proposals.csv | grep -oP 'P-\d{8}-\K\d+' | sort -n | tail -1
```
