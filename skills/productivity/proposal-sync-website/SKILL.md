---
name: proposal-sync-website
description: 提案系统（proposal-index.md）单向同步到项目管理系统（GitHub data/proposals.json）— 项目→提案两层结构
---

# Proposal System Sync Skill

## Purpose

单向同步提案管理系统（`~/.hermes/proposals/proposal-index.md`）元数据到项目管理系统（GitHub 仓库 `data/proposals.json`）。

**注意：网站已于 2026-04-19 从「扁平提案」重构为「项目→提案」两层结构。**

## 数据格式（v2）

```json
{
  "version": 2,
  "projects": [
    {
      "id": "PRJ-YYYYMMDD-XXX",
      "name": "项目名称",
      "description": "项目描述",
      "url": "https://...",           // 项目最新访问链接
      "gitRepo": "https://github.com/...",
      "createdAt": "YYYY-MM-DD",
      "updatedAt": "YYYY-MM-DD",
      "proposals": [
        {
          "id": "P-YYYYMMDD-XXX",
          "name": "提案名称",
          "description": "提案描述",
          "type": "web | app | package",
          "status": "active | in_dev | archived",
          "url": "https://...",
          "packageUrl": "https://...",
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

## 迁移说明

v1 格式（已废弃）：
```json
{ "proposals": [{ "id": "P-...", ... }] }
```

v2 格式：每个提案包装成一个项目，项目的 proposals 数组只包含一个提案。

## 同步脚本

`~/.hermes/scripts/sync-proposals-to-website.py`

### 核心逻辑

```python
def parse_proposal_index():
    """从 proposal-index.md 解析提案列表"""
    content = open('/home/hermes/.hermes/proposals/proposal-index.md').read()
    # 每个提案块用 "### P-YYYYMMDD-NNN: title" 开头
    # 块结尾的 lookahead 必须是双换行 + ---: (?=\n\n---\n)
    # ⚠️ 重要：proposal-index.md 中各提案块之间的分隔符是 \n\n---\n（两个换行）
    #    单个 \n---\n 会漏掉第一个块之后的所有提案！
    blocks = re.findall(
        r'(### P-\d{8}-\d{3}:[^\n]*\n)(.*?)(?=\n\n---\n|\Z)',
        content, re.DOTALL
    )
    proposals = []
    for header, body in blocks:
        pid, title = re.match(r'### (P-\d{8}-\d{3}): (.+)', header).group(1, 2)
        fields = dict(re.findall(r'- `([^`]+)`: (.+)', body))
        proposals.append({'pid': pid, 'title': title.strip(), **fields})
    return proposals

def sync_to_github(proposals):
    """同步到 GitHub — 只 PUT data/proposals.json，不碰 dist/src"""
    # 用 GitHub API 获取当前 SHA，PUT 更新文件
    # ⚠️ WSL 网络不稳定时 urllib 会超时，用 gh api 或 curl 作为 fallback
    pass
```

### ⚠️ 已知 Bug：源文件分隔符可能缺失

proposal-index.md 要求各提案块之间必须有 `\n\n---\n` 分隔符。如果某个提案块后缺少分隔符，会导致该提案被下一个提案的内容覆盖或丢失。

**检查方法：**
```bash
grep -n 'P-' ~/.hermes/proposals/proposal-index.md
# 正常输出：两个提案ID之间隔着 ---

# 异常输出（缺少分隔符）：
#   5: ### P-20260422-001: 项目A
#   6: ... Acceptance: accepted
#   7: ### P-20260422-002: 项目B   ← 中间没有 ---
```

**修复方法（patch 工具失效时用 standalone 脚本）：**
```python
# fix_separator.py — 写入文件后 python3 fix_separator.py
content = open('/home/hermes/.hermes/proposals/proposal-index.md').read()
old = '`Acceptance`: accepted\n\n### P-YYYYMMDD-NNN: 下一提案标题'
new = '`Acceptance`: accepted\n\n---\n\n### P-YYYYMMDD-NNN: 下一提案标题'
if old in content:
    content = content.replace(old, new, 1)
    open('/home/hermes/.hermes/proposals/proposal-index.md', 'w').write(content)
    print('Separator fixed!')
```

**patch 工具失效的典型错误：**
- `"Found N matches for old_string. Provide more context..."` → 添加更多上下文
- `"old_string and new_string are identical"` → 说明 old_string 在文件中已匹配成功，但替换未执行；需要用上述 Python 脚本直接操作

### ⚠️ sync 脚本的正则 Bug（已修复，但需知其原理）

旧版脚本使用 `(?=\n---\n)` 检查分隔符，但实际分隔符是 `\n\n---\n`（前面有两个换行）。这导致只有第一个提案块被正确提取，后续所有提案都被漏掉。

**症状：** 脚本报告 "从提案索引提取了 N 个提案"，但 GitHub 上只收到 N-1 个（永远少一个）。

**修复：** lookahead 改为 `(?=\n\n---\n)`。此 bug 已修复在 `~/.hermes/scripts/sync-proposals-to-website.py` 中。

### 实际网站 JSON 格式（v2 — 嵌套结构）

```json
{
  "version": 2,
  "projects": [
    {
      "id": "PRJ-20260428-001",
      "name": "whack-a-mole-3d",
      "description": "3D打地鼠",
      "url": "https://yeluo45.github.io/whack-a-mole-3d/",
      "gitRepo": "https://github.com/YeLuo45/whack-a-mole-3d",
      "createdAt": "2026-04-28",
      "updatedAt": "2026-04-28",
      "proposals": [
        {
          "id": "P-20260430-003",
          "name": "whack-a-mole-3d",
          "type": "package",
          "status": "active",
          "url": "https://yeluo45.github.io/whack-a-mole-3d/",
          "gitRepo": "https://github.com/YeLuo45/whack-a-mole-3d",
          "tags": ["提案"],
          "createdAt": "2026-05-01",
          "updatedAt": "2026-05-01",
          "prdConfirmation": "timeout-approved"
        }
      ]
    }
  ]
}
```

**关键字段位置：**
- `prdConfirmation` → `projects[n].proposals[n].prdConfirmation`
- `techExpectations` → `projects[n].proposals[n].techExpectations`
- `acceptance` → `projects[n].proposals[n].acceptance`（注意不是项目顶层）

**注意：**
1. `prdConfirmation` 和 `techExpectations` 字段位于嵌套 `proposals[]` 数组内的 proposal 对象上，**不是**项目顶层字段
2. v2 实际是 `projects[].proposals[]` 两层结构，每个 project 的 `proposals[]` 数组通常只含一个提案
3. `generate_proposals_json.py` 生成的扁平格式（project 直接包含所有字段）与实际 GitHub JSON 结构不一致 — 前者是简化版，后者是完整嵌套版

### 状态映射

```python
# 新增状态：in_tdd_test, in_test_acceptance, test_failed → in_dev
#           deploying, deployed → active
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

**说明：**
- `in_tdd_test`（测试用例生成中）、`in_test_acceptance`（测试验收中）、`test_failed`（测试失败）均视为开发中状态
- `deploying`（部署中）、`deployed`（已部署）均视为已完成上线状态
- `research_direction_pending`（等待迭代方向确认）视为开发中状态

### 名称推断

```python
if github_repo:
    name = extract_repo_name(github_repo)  # 从 URL 提取
elif project_path:
    name = extract_from_path(project_path)  # 从路径提取
else:
    name = slugify(title)  # 从中文标题生成
```

## 定时同步 Cron Job

- Job ID: `deaa66b08f2d`
- 每天 9:00 和 18:00 执行
- 交付方式: local（不推送通知）
- 脚本路径: `/home/hermes/.hermes/scripts/sync-proposals-to-website.py`

## 网络故障排除

### Python urllib 超时
脚本使用 `urllib.request.urlopen` 连接 GitHub API 超时（SSL handshake timeout）时：

```bash
# 用 gh api 作为 fallback 手动同步
# 1. 获取当前 SHA
SHA=$(gh api repos/YeLuo45/proposals-manager/contents/data/proposals.json --jq '.sha')

# 2. 生成 v2 数据并 base64 编码后上传
gh api repos/YeLuo45/proposals-manager/contents/data/proposals.json \
  --method PUT \
  --field message="sync: 更新提案数据" \
  --field content="$(python3 -c "
import json
# 读取 proposal-index.md 并解析为 v2 格式
..." | base64)" \
  --field sha="$SHA"
```

### ⚠️ GitHub API PUT 失败：Bad credentials (401)

**症状：** 使用 `gh api --field content@file.json` 报错 `invalid key: "content@file.json"`

**原因：** gh api 的 `@` 语法只在部分版本支持，且不支持通过 pipe 传入 token

**正确做法：** Python urllib + gh auth token
```python
import urllib.request, json, base64, subprocess

# 读取本地 JSON
with open('data/proposals.json') as f:
    new_content = f.read()

new_content_b64 = base64.b64encode(new_content.encode()).decode()

# 获取当前 SHA
url = "https://api.github.com/repos/YeLuo45/proposals-manager/contents/data/proposals.json"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
    sha = data['sha']

# 获取 gh token 并推送
token = subprocess.check_output(['gh', 'auth', 'token']).decode().strip()
payload = json.dumps({
    "message": "chore: 更新提案数据",
    "content": new_content_b64,
    "sha": sha
}).encode()

update_req = urllib.request.Request(url, data=payload, headers={
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}, method='PUT')

with urllib.request.urlopen(update_req, timeout=30) as resp:
    result = json.loads(resp.read().decode())
    print("SUCCESS:", result['commit']['sha'])
```

### GitHub API Rate Limit
```
{"message":"API rate limit exceeded for 149.34.251.244..."}
```
等待几分钟后再试，或使用 `gh api --paginate` 认证请求。

## WSL 网络不稳定时的 Fallback

WSL 的 DNS (`/etc/resolv.conf`) 可能间歇性故障，导致 `urllib`、`gh`、`git` 等全部超时，但浏览器可能仍可访问 GitHub（走不同的 DNS 路径）。

**优先用浏览器编辑：**
```url
https://github.com/YeLuo45/proposals-manager/edit/main/data/proposals.json
```

**本地生成 JSON（不依赖网络）：**
如果 sync 脚本因网络问题卡住，可以：
1. 用 `generate_proposals_json.py` 生成本地 JSON（保存在 `~/.hermes/scripts/proposals.json`）
2. 等网络恢复后，用浏览器粘贴到 GitHub 编辑器

```python
# ~/.hermes/scripts/generate_proposals_json.py — 生成本地 proposals.json
# 用途：网络故障时生成正确格式的 JSON，等恢复后手动推送
```

**网络检测（快速判断）：**
```bash
curl --max-time 5 https://api.github.com  # 超时 = 网络问题
gh auth status                              # 超时 = 网络问题
```

## 验证同步结果

```bash
# 检查 GitHub API 返回的文件内容
curl -s https://api.github.com/repos/YeLuo45/proposals-manager/contents/data/proposals.json

# 或用 gh api（不会 rate limit）
gh api repos/YeLuo45/proposals-manager/contents/data/proposals.json --jq '.content' | base64 -d | python3 -m json.tool | head -30

# 打开网站验证（需输入 GitHub Token）
open https://yeluo45.github.io/proposals-manager/
```

### 网站显示"请输入 GitHub Token"
这是正常的安全设计。浏览器访问网站需输入 GitHub PAT（需 repo 权限）才能解密并显示提案数据。

## 回滚

如需回滚到 v1 格式（扁平提案），找到 git commit SHA 后：
```bash
git show <commit-SHA>:data/proposals.json > data/proposals.json
git commit -m "回滚到 v1 扁平提案格式"
git push origin main --force
```
