# Git Push 网络阻塞与 REST API 上传经验总结

## 本 session 核心发现

### 1. Git Push 完全阻塞时的完整解决方案

**症状**：HTTPS push 返回 HTTP 408，GnuTLS EOF，SSH 端口 22 超时。
**解决**：GitHub REST API `PUT /repos/{owner}/{repo}/contents/{path}`

```python
import subprocess, json, base64, urllib.request, os, time

TOKEN = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip()

def get_sha(repo, path):
    """获取文件 SHA（更新已存在文件时必须）"""
    url = f'https://api.github.com/repos/yeluo45/{repo}/contents/{path}'
    req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get('sha')
    except:
        return None

def upload_file(repo, path, content):
    """上传单个文件"""
    url = f'https://api.github.com/repos/yeluo45/{repo}/contents/{path}'
    sha = get_sha(repo, path)
    payload = json.dumps({
        'message': f'add {path}',
        'content': base64.b64encode(content).decode(),
        **({} if not sha else {'sha': sha})  # 更新文件必须提供 sha
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={'Authorization': f'token {TOKEN}', 'Content-Type': 'application/json'}, method='PUT')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)[:80]}

# 使用
for repo, proj_path in [("my-repo", "/path/to/project")]:
    for fpath in files_to_upload:
        full = f"{proj_path}/{fpath}"
        with open(full, 'rb') as fh:
            content = fh.read()
        result = upload_file(repo, fpath, content)
```

### 2. 关键教训：更新已存在文件必须先获取 SHA

**错误**：
```bash
curl -X PUT -H "Authorization: token $TOKEN" \
  -d "{\"message\":\"update\",\"content\":\"$BASE64\"}" \
  "https://api.github.com/repos/owner/repo/contents/path/file.md"
# → 422 "sha wasn't supplied"
```

**正确**：
```python
sha = get_sha(repo, path)  # 先查 SHA
payload = json.dumps({'message': '...', 'content': b64, 'sha': sha})
```

### 3. Rate Limit 差异巨大

| 请求类型 | Rate Limit |
|---------|-----------|
| 未认证 | 60 req/hr |
| `gh auth token` 认证 | 5,000 req/hr |

**结论**：始终用 `gh auth token` 获取认证 token。

### 4. gh repo create --source 会导致 "Unable to add remote origin"

```bash
# 错误：会尝试添加已存在的 origin
gh repo create yeluo45/repo --public --source=/path/to/repo
# → X Unable to add remote "origin"

# 正确：只创建仓库，本地手动 push
gh repo create yeluo45/repo --public
cd /path/to/repo && git push -u origin master
```

### 5. pnpm workspace 导致 node_modules 被 git 跟踪

**症状**：`git ls-files | grep -c node_modules` 返回 4912+

**原因**：pnpm workspace 的 `docs-site/node_modules/.pnpm/` 被 git 跟踪

**修复**：
```bash
git rm -r --cached docs-site/node_modules
echo "node_modules/" >> .gitignore
git add .gitignore && git commit -m "chore: remove node_modules"
```

**验证**：`git ls-files | grep -c node_modules` 应为 0

### 6. 远程分支名 main vs master 的坑

**问题**：远程默认分支是 `main` 而非 `master`，导致：
```bash
git push -u origin master:main
# → ! [rejected] master -> main (non-fast-forward)
```

**解决**：
```bash
# 方案 A：强制推送到 main（需要用户批准）
git push -f origin master:main

# 方案 B：推送到新分支
git push -u origin master:site

# 方案 C：先用 fetch 获取远程 SHA，然后 REST API
git fetch origin main
# REST API 用 remote_sha 作为 parent，force=false 也能成功
```

**注意**：`gh repo sync` 只能把远程同步到本地，无法解决"本地想强制覆盖远程"的场景。

### 7. 递归列出远程文件找缺失

**需求**：需要知道本地哪些文件尚未上传到远程

```python
def list_remote_recursive(repo, path=''):
    url = f'https://api.github.com/repos/yeluo45/{repo}/contents/{path}'
    req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                result = []
                for item in data:
                    if item['type'] == 'file':
                        result.append(f"{path}/{item['name']}".strip('/') if path else item['name'])
                    elif item['type'] == 'dir':
                        subpath = f"{path}/{item['name']}".strip('/') if path else item['name']
                        result.extend(list_remote_recursive(repo, subpath))
                return result
    except:
        return []
    return []

# 使用
remote_files = set(list_remote_recursive(repo))
local_files = set([...])  # git ls-files
missing = local_files - remote_files
```

### 8. 批量上传时的 API 限流处理

每个请求间加 `time.sleep(2)` 避免触发限流。完整上传 17 个文件约需 2-3 分钟。

### 9. 文件大小限制

- 单文件 > 1MB 需要特殊处理（大文件 blob API 本身有 50MB 限制）
- 实际推送时跳过 > 1MB 的文件

### 10. 验证推送结果

```bash
# 方法 1：检查目录内容数量
curl -s --max-time 10 "https://api.github.com/repos/yeluo45/$repo/contents/" | grep -c '"name"'

# 方法 2：递归检查所有文件
curl -s "https://api.github.com/repos/yeluo45/$repo/git/trees/main?recursive=1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'tree items: {len(d.get(\"tree\",[]))}')"

# 方法 3：检查 raw 文件
curl -s --max-time 10 "https://raw.githubusercontent.com/YeLuo45/$repo/main/README.md" | head -3
```

### 11. GitHub Actions 触发

如果 `.github/workflows/deploy.yml` 已就位但 GitHub Pages 没开始部署，可以手动触发：

```bash
gh api --method POST "repos/yeluo45/{repo}/actions/workflows/deploy.yml/dispatches" \
  -f ref="main" 2>&1
# → 204 No Content = 成功
```

### 12. 本 session 最终结果

10 个 design 项目全部通过 REST API 上传完成：

| 项目 | 文件数 |
|------|--------|
| generic-agent-design | 45 |
| open-space-design | 37 |
| scrapling-design | 18 |
| claude-code-design | 21 |
| claudecodesrc-design | 17 |
| freqtrade-develop-design | 14 |
| langcli-design | 14 |
| ohmypi-design | 23 |
| opencode-dev-design | 19 |
| ruflo-design | 24 |

耗时约 25 分钟（大部分是网络等待）。