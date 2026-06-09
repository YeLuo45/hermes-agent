# Website Sync & GitHub Reference

## Website & GitHub

| Item | Value |
|------|-------|
| Website | https://yeluo45.github.io/prj-proposals-manager/ |
| Website title | 项目提案管理（不是"提案管理"） |
| GitHub repo | YeLuo45/prj-proposals-manager (master 分支存源码，gh-pages 分支存部署) |
| hermes-agent repo | YeLuo45/hermes-agent (proposals 变更同步到此处) |
| Data file | `data/proposals.json` on master — **flat array of proposals** under `projects` key: `{version: 2, projects: [{id, name, projectId, status, type, createdAt, updatedAt, gitRepo, deploymentUrl, description}]}`。每个提案的 `projectId` 字段指向真实项目（如 `PRJ-20260412-009`）。`p-*` 格式的 projectId 是孤儿提案（非真实项目）。 |
| Favorites data | `data/favorites.json` (收藏数据，格式: `{favorites: {projectId: {timestamp, pinned, group}}, groups: [{id, name, color}], updatedAt}`) |
| GitHub Token | `$GITHUB_TOKEN`（环境变量，placeholder 用于文档；实际 token 在 `~/.hermes/tools/github-token.txt`）|

## Website CSV Import Validation (CRITICAL — Different from Internal States)

**网站 CSV 导入验证枚举（与内部工作流状态不同）：**
- `status` 有效值：`active`、`in_dev`、`archived`（不是 `delivered/approved_for_dev` 等）
- `type` 有效值：`web`、`app`、`package`（不是 `feature/proposal` 等）

**内部状态 → 网站枚举映射规则：**
| 内部状态 | 网站映射 | 说明 |
|---------|---------|------|
| `delivered` / `deployed` / `accepted` | `active` | 已发布的特性 |
| `approved_for_dev` / `intake` / `in_dev` 相关 | `in_dev` | 开发中 |
| `archived` | `archived` | 归档（保持不变） |

**同步前必须检查/修复的字段：**
1. `status` — 必须是 `active`/`in_dev`/`archived` 之一
2. `type` — 必须是 `web`/`app`/`package` 之一（从项目类型推导）
3. `last_update` — 必须是 `YYYY-MM-DD` 格式（可从 P-ID `P-YYYYMMDD-XXX` 推导）
4. 重复 ID — `proposals.csv` 内不允许重复 P-ID

## Data Flow Strategy (Local-First)

**数据流向（已更新）**:
```
本地 proposal-index.md → sync-proposals-to-website.py → GitHub data/proposals.json
                                       ↓
                    (本地有提案 → 以本地数据为准推送；
                     本地无提案 → 以 GitHub 为 fallback)
```

**sync-proposals-to-website.py 行为：**
1. 读取 `proposal-index.md` (本地) 提取提案
2. 调用 GitHub API 获取 `data/proposals.json` 现有数据
3. **合并策略**：
   - 本地有提案 → 以本地数据为准构建推送（覆盖 GitHub）
   - 本地无提案 → 以 GitHub 数据为 fallback
4. **推送 GitHub** `data/proposals.json`
5. **拉回 GitHub** 最新数据，重新生成 CSV 到本地

**这意味着：**
- **本地 CSV 修复会自动同步到 GitHub**（sync 脚本以本地为 source of truth）
- **本地 markdown 修复也会直接生效**
- **最可靠的方式**：直接通过 GitHub API 修复 `data/proposals.json`

## ⚠️ CRITICAL: Sync Script Corruption Bug (2026-05-14 发现)

**sync-proposals-to-website.py 有两类 bug**：

### Bug 1: String Corruption (return '\n'.join(lines) Split)

**症状**：
```
File "sync-proposals-to-website.py", line 197
    return '
           ^
SyntaxError: unterminated string literal (detected at line 197)
```

**根因**：文件中的 `return '\n'.join(lines)` 有时被拆分成多行。

**修复方法**：
```python
with open('scripts/sync-proposals-to-website.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

fixed_lines = []
i = 0
while i < len(lines):
    if lines[i].strip() == "return '" and i+1 < len(lines) and lines[i+1].strip() == "'.join(lines)":
        fixed_lines.append("    return '\\n'.join(lines)")
        i += 2
    else:
        fixed_lines.append(lines[i])
        i += 1

with open('scripts/sync-proposals-to-website.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))
```

### Bug 2: group_by 解析 bug (已记录)

**症状**：gh-pages 上的 `data/proposals.json` 变成 15 个乱码项目（而非预期的 45 个），项目 ID 被污染成类似 `ai-subscription`on`、`card-game-prototype`ivation-simulator` 的乱码。

**根因**：当项目名包含中文顿号 `、` 时，split 分隔逻辑错误地将 `project_name` 截断，污染了项目 ID 生成。

**修复前应对**：
1. **不要运行 sync-proposals-to-website.py**，否则会再次破坏数据
2. 直接用干净版本覆盖 GitHub 的 `data/proposals.json`（见上方 Direct GitHub API Fix）
3. 修复 sync 脚本的 group_by 逻辑后，才能重新启用 sync

**验证方法**：
```bash
python3 -c "
import json
with open('data/proposals.json') as f:
    d = json.load(f)
for p in d['projects']:
    if 'id' not in p: p['id'] = p['name']
print(f'projects={len(d[\"projects\"])}, proposals={sum(len(p.get(\"proposals\",[])) for p in d[\"projects\"])}')
# 期望: projects=45, proposals=214
# 如 projects=15 且名称含乱码 = 被 sync 脚本破坏
"
```

**推荐替代方案**：禁用 sync 脚本的 proposal-index.md 解析，直接 commit 干净的 `data/proposals.json` 到 master 分支。GitHub Actions deploy.yml 会自动 build + deploy。

## Direct GitHub API Fix (Recommended)

```python
import urllib.request, json, base64

TOKEN = 'ghp_YOUR_TOKEN'
REPO = 'YeLuo45/prj-proposals-manager'
DATA_PATH = 'data/proposals.json'

def get_sha(path):
    url = f'https://api.github.com/repos/{REPO}/contents/{path}'
    req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())['sha']

# GET current
sha = get_sha(DATA_PATH)
url = f'https://api.github.com/repos/{REPO}/contents/{DATA_PATH}'
req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
with urllib.request.urlopen(req) as r:
    content = base64.b64decode(json.loads(r.read())['content']).decode('utf-8')
    data = json.loads(content)

# Fix: delivered->active, approved_for_dev->in_dev, type清理, 日期清理
for p in data.get('projects', []):
    if p.get('status') == 'delivered': p['status'] = 'active'
    elif p.get('status') == 'approved_for_dev': p['status'] = 'in_dev'
    if p.get('type') in ['proposal', 'feature', 'bugfix']: p['type'] = 'web'
    # 修复 None/'' 日期
    import re
    pid = p.get('id', '')
    mm = re.match(r'P-(\d{4})(\d{2})(\d{2})-\d{3}', pid)
    if mm and not p.get('createdAt'):
        p['createdAt'] = f'{mm.group(1)}-{mm.group(2)}-{mm.group(3)}'
    if mm and not p.get('updatedAt'):
        p['updatedAt'] = f'{mm.group(1)}-{mm.group(2)}-{mm.group(3)}'

# PUT fixed
data_put = json.dumps({
    'message': 'fix: correct status/type/dates',
    'content': base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode(),
    'sha': sha
})
req = urllib.request.Request(url, data=data_put.encode(),
    headers={'Authorization': f'token {TOKEN}', 'Content-Type': 'application/json'}, method='PUT')
with urllib.request.urlopen(req) as r:
    print('Pushed:', json.loads(r.read()).get('commit', {}).get('sha', '?')[:8])
```

## Local CSV Generation (No Push)

```bash
GITHUB_TOKEN=$GITHUB_TOKEN \
  python3 ~/.hermes/scripts/sync-proposals-to-website.py --csv-only
```

## Orphan Proposals (p-* projectId) — Common Bug Pattern

`data/projects` 是扁平提案数组，不是嵌套项目数组。`projectId` 为 `p-*` 格式的提案是孤儿提案（ID指向不存在的项目）。前端分组时必须识别并合并：

```
真实项目：projectId 以 PRJ- 开头
孤儿提案：projectId 以 p- 开头或为空 → 应归入 __ORPHAN__ 组
```

**错误做法**：为每个孤儿提案创建独立分组，导致"项目数量超预期"。

## GitHub Repo Branch Strategy

| Branch | Purpose |
|--------|---------|
| `master` | Source code (Vite build files) |
| `gh-pages` | **Deployed website content** — GitHub Pages serves from here |

**CRITICAL**: `sync-proposals-to-website.py` pushes to `gh-pages` branch by default. GitHub Pages reads from `gh-pages`, NOT `master`. When verifying data:
- Website (live): `https://yeluo45.github.io/prj-proposals-manager/data/proposals.json`
- Raw file (gh-pages): `https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/gh-pages/data/proposals.json`
- API (master default): `https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json` → use `?ref=gh-pages` to target deployed content

## URL Path Note

GitHub Pages 部署在子路径 `/prj-proposals-manager/`（末尾有斜杠）。`window.location.pathname` 返回 `/prj-proposals-manager/`。拼接 data URL 时必须 strip 末尾斜杠：`pathname.replace(/\/$/, '')` 得到 `/prj-proposals-manager`，再拼 `${origin}${basePath}/data/proposals.json` = `https://yeluo45.github.io/prj-proposals-manager/data/proposals.json`。

## prj_url Inference from git_repo

`prj_url` is inferred from `git_repo` field. Only `github.com/YeLuo45/*` repos get a URL. Pattern:
- `https://github.com/YeLuo45/{repo}` → `https://yeluo45.github.io/{repo}`
- Exception: repos requiring trailing slash (`generic-agent-design`, `ruflo-design`) → `https://yeluo45.github.io/{repo}/`

**Inference code (Python):**
```python
import re
def git_repo_to_url(git_repo):
    if not git_repo or not git_repo.strip():
        return ''
    match = re.search(r'github\.com[/:]([^/]+)/([^/\.]+)', git_repo)
    if match and match.group(1) == 'YeLuo45':
        repo = match.group(2)
        if repo in ['generic-agent-design', 'ruflo-design']:
            return f'https://yeluo45.github.io/{repo}/'
        return f'https://yeluo45.github.io/{repo}'
    return ''
```

## Sync to hermes-agent

推送 proposals 变更到 hermes-agent：
```bash
cd /home/hermes/.hermes
git checkout -b feature/hermes$(date +%y%m%d)
git add proposals/
git commit -m "sync: update proposals from hermes-agent $(date +%Y-%m-%d)"
git push -u https://YeLuo45:***@github.com/YeLuo45/hermes-agent.git feature/hermes$(date +%y%m%d)
```
- 分支命名格式：`feature/hermesYYMMDD`（如 `feature/hermes260505`）
- 推送目标：`https://github.com/YeLuo45/hermes-agent`
- 只推送 `proposals/` 目录的变更，不碰其他源码
