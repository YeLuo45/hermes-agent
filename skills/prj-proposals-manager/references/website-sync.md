# Website Sync & GitHub Reference

## Website & GitHub

| Item | Value |
|------|-------|
| Website | https://yeluo45.github.io/prj-proposals-manager/ |
| Website title | 项目提案管理（不是"提案管理"） |
| GitHub repo | YeLuo45/prj-proposals-manager (master 分支存源码，gh-pages 分支存部署) |
| hermes-agent repo | YeLuo45/hermes-agent (proposals 变更同步到此处) |
| Data file | `data/proposals.json` on master (v2 格式: `{version: 2, projects: [{name, url, gitRepo, proposals: [...]}]}`) |
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

**数据流向（已更新）：**
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
for proj in data.get('projects', []):
    for p in proj.get('proposals', []):
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

## URL Path Note

GitHub Pages 部署在子路径 `/prj-proposals-manager/`（末尾有斜杠）。`window.location.pathname` 返回 `/prj-proposals-manager/`。拼接 data URL 时必须 strip 末尾斜杠：`pathname.replace(/\/$/, '')` 得到 `/prj-proposals-manager`，再拼 `${origin}${basePath}/data/proposals.json` = `https://yeluo45.github.io/prj-proposals-manager/data/proposals.json`。

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
