---
name: proposal-sync-website
description: 提案系统（proposal-index.md）单向同步到项目管理系统（GitHub data/proposals.json）— 项目→提案两层结构
---

# Proposal System Sync Skill

## Purpose

单向同步提案管理系统（`~/.hermes/proposals/proposal-index.md`）元数据到 GitHub 仓库 `data/proposals.json`。

**网站已于 2026-04-19 从「扁平提案」重构为「项目→提案」两层结构。**

## 数据格式（v2）

```json
{
  "version": 2,
  "projects": [
    {
      "id": "PRJ-YYYYMMDD-XXX",
      "name": "项目名称",
      "description": "项目描述",
      "url": "https://...",
      "gitRepo": "https://github.com/...",
      "createdAt": "YYYY-MM-DD",
      "updatedAt": "YYYY-MM-DD",
      "proposals": [
        {
          "id": "P-YYYYMMDD-XXX",
          "name": "提案名称",
          "type": "web | app | package",
          "status": "active | in_dev | archived",
          "url": "https://...",
          "gitRepo": "https://github.com/...",
          "tags": ["标签1"],
          "createdAt": "YYYY-MM-DD",
          "updatedAt": "YYYY-MM-DD",
          "prdConfirmation": "confirmed | pending | timeout-approved",
          "techExpectations": "confirmed | pending | timeout-approved",
          "acceptance": "pending | passed | failed"
        }
      ]
    }
  ]
}
```

**关键字段位置：** `prdConfirmation`、`techExpectations`、`acceptance` 在 `projects[n].proposals[n]` 上，**不是**项目顶层。

## 同步脚本

`~/.hermes/scripts/sync-proposals-to-website.py`

**注意：** proposal-index.md 维护规范（插入/修改提案条目、separator 检查）见 `references/proposal-index-maintenance.md`。

### 核心逻辑

1. `parse_proposal_index()` — 从 proposal-index.md 解析提案列表（用双换行 `\\n\\n---\\n` 分隔符）
2. `sync_to_github()` — PUT data/proposals.json，**不碰 dist/src**

已知已修复：正则 lookahead 之前用 `(?=\\n---\\n)` 导致漏掉提案，已改为 `(?=\\n\\n---\\n)`。

### 状态映射

```python
if proposal_status in ["accepted", "delivered", "deploying", "deployed"]:
    web_status = "active"
elif proposal_status in [
    "in_dev", "in_acceptance", "approved_for_dev",
    "in_tdd_test", "in_test_acceptance", "test_failed",
    "research_direction_pending"
]:
    web_status = "in_dev"
else:
    web_status = "archived"
```

## 网络故障排除

### urllib 超时 → 用 curl fallback

```python
import subprocess
cmd = ['curl', '-s', '-L', '--max-time', '30', '-X', 'PUT',
       '-H', f'Authorization: Bearer {token}',
       '-H', 'Content-Type: application/json',
       '-d', json.dumps(data), url]
result = subprocess.run(cmd, capture_output=True, text=True)
```

### SHA 过时 → PUT 前先 GET

每次 PUT 前先 GET 获取最新 sha，捕获 409 后重试。

### Bad credentials (401)

gh api 的 `@` 语法不支持通过 pipe 传 token。用 Python urllib + `gh auth token` 获取 token。

### Rate Limit

等待几分钟，或用 `gh api --paginate` 认证请求。

### WSL DNS 间歇性故障

`urllib`/`gh`/`git` 全超时但浏览器可能通。优先用浏览器编辑：
```
https://github.com/YeLuo45/prj-proposal-management/edit/main/data/proposals.json
```

## 验证同步结果

```bash
# 检查 GitHub API 返回
gh api repos/YeLuo45/prj-proposal-management/contents/data/proposals.json \
  --jq '.content' | base64 -d | python3 -m json.tool | head -30

# 打开网站验证
open https://yeluo45.github.io/prj-proposal-management/
```

## 双层 Bug 诊断

网站数据异常时同时排查两层：

**第一层：前端解析** — `App.jsx` 检查 `data.projects`（v2）还是 `data.proposals`（v1）

**第二层：sync 脚本配置** — `REPO_NAME` 是否匹配实际仓库名

诊断：对比 raw.githubusercontent.com 的提案数量与 proposal-index.md 的数量。

## 回滚

```bash
git show <commit-SHA>:data/proposals.json > data/proposals.json
git commit -m "回滚到 v1 扁平提案格式"
git push origin main --force
```
