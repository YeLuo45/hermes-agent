# Design 项目子 Agent 并行执行与 GitHub API 推送

> 本文档沉淀自 hermes-agent-design 迭代经验（2026-05-13）

---

## 1. Subagent 并行执行：batch size = 3

当需要并行委托多个子任务时，`delegate_task` 的 `max_concurrent_children` 限制为 **3 个**。

**教训**：最初尝试一次性委托 6 个 HTML 页面创建任务（api/dashboard/mcp/agent-runner/platform-adapter/plugin-development），被拒绝：
```
Too many tasks: 6 provided, but max_concurrent_children is 3.
```

**正确做法**：分批委托，每批 ≤ 3 个任务。

```python
# 第一批：3 个页面
delegate_task(tasks=[api_task, dashboard_task, mcp_task])

# 第二批：3 个页面
delegate_task(tasks=[agent_runner_task, platform_adapter_task, plugin_dev_task])
```

---

## 2. GitHub API 推送：SHA-first PUT /contents 模式

### 2.1 场景

当 `git push` 超时或被阻塞时，可用 GitHub REST API 推送文件。

### 2.2 已有仓库（已有 commit 历史）

hermes-agent-design 案例：远程已有 commit 历史，需要上传/更新 11 个文件，git push --force 超时。

**核心问题**：更新已有文件必须提供 SHA，否则 422。

```python
import base64, urllib.request, json

with open('/home/hermes/.hermes/profiles/onepc/home/.git-credentials') as f:
    token = f.read().split('x-access-token:')[1].split('@')[0].strip()

OWNER, REPO = 'YeLuo45', 'hermes-agent-design'

def get_file_sha(path):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Authorization': f'token {token}'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())['sha']
    except:
        return None  # 文件不存在

def update_file(path, content, sha=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    payload = {
        "message": "commit message",
        "content": base64.b64encode(content.encode()).decode()
    }
    if sha:
        payload["sha"] = sha  # 更新已有文件必须提供 SHA
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'Mozilla/5.0',
        'Authorization': f'token {token}',
        'Content-Type': 'application/json'
    }, method='PUT')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

# 使用
files = ['README.md', 'index.html', 'api.html', ...]
for f in files:
    sha = get_file_sha(f)       # 先获取远程 SHA
    update_file(f, content, sha=sha)  # sha=None 时创建，sha 存在时更新
```

**关键点**：
- `sha=None` → GitHub API 创建新文件
- `sha=<remote_sha>` → GitHub API 更新已有文件
- 不提供 SHA 就更新会报 422

---

## 3. GitHub Pages 手动触发构建

### 3.1 问题症状

workflow 文件存在但 builds 列表为空，从未被触发过。

```bash
gh api repos/YeLuo45/hermes-agent-design/pages/builds/latest
# → 404 Not Found
```

### 3.2 手动触发

```bash
curl -s -X POST \
  -H "Authorization: Bearer $(gh auth token)" \
  https://api.github.com/repos/YeLuo45/hermes-agent-design/pages/builds
# → {"status": "queued", "url": "..."}
```

### 3.3 验证部署

```bash
sleep 20 && curl -s -o /dev/null -w "%{http_code}" \
  https://yeluo45.github.io/hermes-agent-design/
# → 200 = 成功
```

### 3.4 检查所有页面

```bash
for page in index api dashboard mcp agent-runner platform-adapter plugin-development; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://yeluo45.github.io/hermes-agent-design/${page}.html")
  echo "$page.html: $code"
done
```

---

## 4. Subagent 完成后的手动收尾清单

| 工作 | 原因 |
|------|------|
| 更新 index.html 添加导航栏 | Subagent 各自创建新页面，不修改 index.html |
| git add + commit | Subagent 不做 git 操作 |
| 推送代码 | 需要主 Agent 执行 |
| 触发 GitHub Pages 构建 | 需要主 Agent 调用 API |

**教训**：委托任务时在 context 中明确说明"不要修改 index.html"，避免 subagent 之间冲突。

---

## 5. 纯 HTML 文档站导航栏模式

hermes-agent-design 使用纯 HTML（无 VitePress），所有 7 个页面共享完全相同的导航栏 HTML 片段：

```html
<style>
.nav {
  background: #1a1a2e;
  padding: 15px 20px;
  text-align: center;
  border-bottom: 1px solid #2a2a4a;
}
.nav a {
  color: #00d4ff;
  text-decoration: none;
  margin: 0 15px;
  font-size: 0.95em;
}
.nav a:hover { text-decoration: underline; }
.nav a.active { color: #fff; font-weight: bold; }
</style>
<body>
<div class="nav">
  <a href="index.html">首页</a> |
  <a href="api.html">API</a> |
  <a href="dashboard.html">Dashboard</a> |
  <a href="mcp.html">MCP</a> |
  <a href="agent-runner.html">Agent Runner</a> |
  <a href="platform-adapter.html">平台适配器</a> |
  <a href="plugin-development.html">插件开发</a>
</div>
```

**规则**：所有 HTML 页面共享完全相同的导航栏 HTML 片段，样式内联在 `<style>` 标签中。
