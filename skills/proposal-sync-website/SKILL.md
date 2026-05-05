---
name: proposal-sync-website
description: 提案系统（proposal-index.md）单向同步到项目管理系统（GitHub data/proposals.json）的完整流程。包含脚本使用、Github API JSON 解析坑点、以及 cron job 配置。
---

# Proposal Sync Website

## 概述

将本地提案索引 `~/.hermes/proposals/proposal-index.md` 同步到 GitHub 仓库的 `data/proposals.json`，供静态网站 `prj-proposals-manager` 读取展示。

**目标仓库**：`YeLuo45/prj-proposals-manager`（不是 proposals-manager）

---

## 同步脚本

### 脚本位置
```
~/.hermes/scripts/sync-proposals-to-website.py
```

### 关键配置（已修复）
```python
REPO_OWNER = "YeLuo45"
REPO_NAME = "prj-proposals-manager"
DATA_FILE_PATH = "data/proposals.json"
BRANCH = "master"
```

### 执行方式
```bash
cd /home/hermes/.hermes/scripts
GITHUB_TOKEN=<YOUR_GITHUB_TOKEN> python3 sync-proposals-to-website.py
```

### 坑点：REPO_NAME 必须匹配
脚本硬编码了 `REPO_NAME`，如果目标仓库改名或创建了错误的仓库，必须手动 patch 此变量。

---

## GitHub API 获取 JSON 文件的正确方式

### 坑：base64 content 可能截断

直接用 curl 管道传给 `json.loads` 会失败：

```bash
# ❌ 错误：JSONDecodeError: Unterminated string
curl -sL "https://api.github.com/repos/.../contents/...?ref=master" | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])"

# ✅ 正确：先保存到文件，再解析
curl -sL --max-time 30 -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/.../contents/data/proposals.json?ref=master" \
  -o /tmp/gh_proposals.json
```

### Python 解析（含截断修复）
```python
import json, base64

with open('/tmp/gh_proposals.json') as f:
    d = json.load(f)

content = d['content']
# base64 可能因特殊字符（中文/换行）导致截断，补充 padding
missing = (4 - len(content) % 4) % 4
content += '=' * missing

try:
    c = base64.b64decode(content).decode('utf-8')
    gh = json.loads(c)
except json.JSONDecodeError:
    # 降级：找最后一个完整 JSON 对象（括号深度追踪）
    depth = 0
    last_complete = 0
    for i, ch in enumerate(c):
        if ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                last_complete = i + 1
    truncated = c[:last_complete]
    gh = json.loads(truncated)
```

---

## Cron Job 配置

### 创建命令
```python
cron(action='create',
     prompt='运行同步脚本，将提案系统（~/.hermes/proposals/proposal-index.md）的数据同步到 GitHub (YeLuo45/prj-proposals-manager) 的 data/proposals.json。\n\n执行步骤：\n1. cd /home/hermes/.hermes/scripts\n2. GITHUB_TOKEN=<YOUR_GITHUB_TOKEN> python3 sync-proposals-to-website.py\n3. 检查输出确认 "成功同步"\n4. 报告同步结果：同步了多少项目/提案',
     schedule='0 9,18 * * *',
     name='提案系统→网站定时同步',
     repeat='forever',
     deliver='local')
```

### 注意
- cron prompt 直接写 python 命令，不依赖 skill 间接调用
- skill（proposal-management）只记录流程，实际执行靠脚本
- schedule 用 cron 表达式（`0 9,18 * * *` = 每天9点和18点）

---

## 静态网站数据读取（网站前端）

网站 `prj-proposals-manager` 前端通过 GitHub API 读取 `data/proposals.json`：

```
GET https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json?ref=master
Headers: Authorization: Bearer <token>
         Accept: application/vnd.github.v3+json
```

响应 body：
```json
{
  "content": "<base64 encoded content>",
  "sha": "<file sha>",
  "encoding": "base64"
}
```

解码后 parse JSON。注意同源策略：GitHub Pages 部署的静态网站需要 GitHub PAT 才能调用 API。

---

## 防止重复项目的机制

### 问题背景
2026-05-04 曾因批量生成提案导致：
1. **11 个 PRJ-20260504-10XX 完全重复**（同一项目两次写入，已修复）
2. **版本碎片化**：同一游戏拆成多个独立项目（game-1024 + game-1024-v2、pixelpal-v4~v17 等）

### 防护措施

#### 1. 版本碎片化合并 `consolidate_related_projects()`
自动检测并合并以下模式：
- **已知主版本映射**：`game-1024-v2` → `game-1024`、`snake-battle-v4` → `snake-battle` 等
- **pixelpal-v* 碎片**：所有 `pixelpal-v4` ~ `pixelpal-v17` → 合并到 `pixel-pal-web` (PRJ-20260420-002)
- **通用版本后缀**：检测 `name-vN` 模式，自动向基础版本合并

#### 2. 精确去重 `check_and_fix_duplicates()`
- **ID 去重**：同一 ID 出现多次时保留字典序最小的条目
- **名称去重**：名称相同但 ID 不同的条目，保留 ID 最小的

#### 3. 同步后验证
- 同步输出显示项目数量和是否有重复警告
- GitHub Actions 自动构建部署网站

### 验证检查清单

同步后验证：
- [ ] GitHub API GET 返回 200 且 sha 变化
- [ ] JSON parse 成功，无截断错误
- [ ] proposals.json 中 `version: 2`，有 `projects` 数组
- [ ] 项目数符合预期（约 40-65 个，非 3 个）
- [ ] 无重复项目（按名称检查）
- [ ] 网站 https://yeluo45.github.io/prj-proposals-manager/ 刷新后显示正确

### 手动验证命令
```python
# 检查重复
python3 -c "
import json, urllib.request, base64
token = '<TOKEN>'
req = urllib.request.Request('https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json',
    headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'})
d = json.loads(base64.b64decode(urllib.request.urlopen(req, timeout=30).read() + b'==').decode())
projects = d.get('projects', [])
names = {}
for p in projects:
    n = p.get('name','')
    if n not in names: names[n] = []
    names[n].append(p.get('id'))
dupes = {n: ids for n, ids in names.items() if len(ids) > 1}
print(f'Total: {len(projects)}, Duplicates: {dupes}')
"
```

## 相关文件路径

## 相关文件路径

| 文件 | 路径 |
|------|------|
| 同步脚本 | `/home/hermes/.hermes/scripts/sync-proposals-to-website.py` |
| 提案索引（生命周期） | `/home/hermes/.hermes/proposals/proposal-index.md` |
| 项目索引（Project→Proposal映射） | `/home/hermes/.hermes/proposals/project-index.md` |
| 提案文档索引 | `/home/hermes/.hermes/proposals/proposal-docs-index.md` |
| GitHub 仓库 | `YeLuo45/prj-proposals-manager` |
| proposals.json 路径 | `data/proposals.json`（master 分支） |
| GitHub Token | `<YOUR_GITHUB_TOKEN>` |

> 注意：`project-index.md` 是本地只读参考，不参与 GitHub 同步。同步是单向的：`proposal-index.md` → `data/proposals.json`。 |
