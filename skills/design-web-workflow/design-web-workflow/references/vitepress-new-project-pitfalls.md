# VitePress New Project Pitfalls

> 2026-05-14 — build-yourownx-design 项目教训
> 2026-05-14 update — posthog-design 项目教训（workflow 未自动触发）
> 2026-05-14 update — thunderbolt-design 项目教训（workflow run 404 + Pages 409）
> 2026-05-14 update — shannon-design 项目教训（workflow dispatch 端点 + 首次失败后 Pages 状态）
> 2026-05-14 update — nanobot-design 项目教训（YAML 冒号 + 双分支 + CI 日志捕获）

## Pitfall 1: theme/index.js 使用了错误的 API

### 错误写法

```js
// ❌ 错误 — 这是 vite.config.js 的写法，不是 theme/index.js
import { defineConfig } from "vitepress";

export default defineConfig({
  extends: DefaultTheme,
});
```

### 正确写法

```js
// ✅ 正确 — theme/index.js 应该 extends DefaultTheme，不需要 defineConfig
import DefaultTheme from "vitepress/theme";
import "./style.css";

export default {
  extends: DefaultTheme,
};
```

### 症状

```
build error:
.vitepress/theme/index.js (1:9): "defineConfig" is not exported by "node_modules/vitepress/dist/client/index.js"
```

### 修复

```bash
git add -A && git commit -m "fix: correct VitePress theme/index.js - extends DefaultTheme"
git push
```

---

## Pitfall 2: Workflow 已创建但未自动触发（total_count: 0）

### 症状

```bash
gh api repos/Owner/repo/actions/runs
# {"total_count":0,"workflow_runs":[]}

curl -s -o /dev/null -w "%{http_code}" https://Owner.github.io/repo/
# 404  (Pages 已配置但 workflow 从未运行)
```

### 根因

GitHub Pages API 启用 build_type: workflow 后，Actions workflow 应在下一次 push 时自动运行。但有时候 workflow 不会被自动触发（尤其是在 `.github/workflows/` 有子目录时）。

### 解决

手动触发 workflow：

```bash
gh workflow run deploy.yml --repo Owner/repo
```

然后等待 30-60 秒验证：

```bash
sleep 45 && curl -s -o /dev/null -w "%{http_code}" https://Owner.github.io/repo/
# 应返回 200
```

### 预防

- 确保 workflow 文件在 `.github/workflows/` 根目录，不要放在子目录
- 不要在 `.github/workflows/` 下创建空子目录（如 `.gitkeep` 子目录）

---

## Pitfall 3: Workflow YAML 的 environment 块导致部署被阻止

### 错误写法

```yaml
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages      # ← 这行导致问题
      url: https://yeluo45.github.io/repo/
    steps:
      - ...
```

### 症状

```
X Branch "main" is not allowed to deploy to github-pages due to environment protection rules.
The deployment was rejected or didn't satisfy other protection rules.
```

### 根因

新仓库首次部署时，GitHub Actions 的 `environment` 块会触发环境保护规则检查。如果这是该 environment 的首次部署，规则可能未配置或配置了保护条件，导致 workflow 被拒绝。

### 正确写法

```yaml
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        working-directory: ./docs-site
        run: pnpm install

      - name: Build
        working-directory: ./docs-site
        run: pnpm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./docs-site/.vitepress/dist

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 修复

1. 从 deploy.yml 中删除 `environment:` 块
2. 推送重新触发 workflow

---

## Pitfall 4: npm install 超时（WSL 本地环境）

### 症状

```bash
npm install  # 在 WSL 中超时，300s killed
```

### 解决

**方案 A（推荐）**：使用 `--prefer-offline` 优先读缓存
```bash
npm install --prefer-offline --no-audit --no-fund
```

**方案 B**：设置 npm registry 为国内镜像
```bash
npm install --registry https://registry.npmmirror.com --no-audit --no-fund
```

---

## Pitfall 5: GitHub Actions 中 npm install 超时

### 症状

```
FAILED: Install dependencies
```

### 解决

```yaml
- name: Cache node modules
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('package.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

- name: Install dependencies
  env:
    NPM_CONFIG_REGISTRY: "https://registry.npmmirror.com"
  run: npm install --prefer-offline --no-audit --no-fund
```

---

## Pitfall 6: Workflow 文件位置导致"Install dependencies"找不到 package.json

### 症状

```
FAILED: Install dependencies
An error occurred trying to start process '/usr/bin/bash' with working directory
'/home/runner/work/{repo}/{repo}/./docs-site'. No such file or directory
```

### 根因

REST API `PUT /repos/{owner}/{repo}/contents/{path}` 中的 `path` 参数决定了文件在仓库中的位置。如果推送时 path 写的是 `package.json` 而不是 `docs-site/package.json`，文件会出现在根目录而非 `docs-site/` 子目录。

### 解决

确保 REST API 推送时 path 前缀正确：
```python
# ✅ 正确
api_put(f"docs-site/package.json", content)
# ❌ 错误（文件会散落在根目录）
api_put("package.json", content)
```

---

## Pitfall 7: nav/sidebar 链接与实际文件名不匹配导致 dead link

### 症状

```
(!) Found dead link /frontend in file README.md
x Build failed: [vitepress] 2 dead link(s) found.
```

### 根因

VitePress 中 `nav` 的 `link` 值必须与**实际文件名**完全匹配（不含 `.md` 扩展名）。

| config.mjs 中写的是 | 实际文件名 | 结果 |
|---------------------|-----------|------|
| `link: "/frontend"` | `frontend-stack.md` | ❌ dead link |
| `link: "/frontend-stack"` | `frontend-stack.md` | ✅ 正常工作 |

### 解决

1. 修改 config.mjs 的 nav/sidebar 让 link 值与实际文件名匹配
2. 启用 `ignoreDeadLinks: true` 作为安全网

---

## Pitfall 8: `gh workflow run` 返回 HTTP 404 但 workflow 文件实际存在

### 症状

```bash
gh workflow run deploy.yml --repo Owner/repo
# HTTP 404: Not Found

curl -s "https://api.github.com/repos/Owner/repo/contents/.github/workflows"
# [{"name": "deploy.yml", ...}]  ← 文件实际存在
```

### 根因

GitHub Actions API 传播延迟。workflow YAML 刚推送后立即执行 `gh workflow run` 可能返回 404。

### 解决（按优先级）

| 方案 | 命令 |
|------|------|
| 等待后重试 | `sleep 45 && gh workflow run deploy.yml --repo Owner/repo` |
| Dummy commit 触发 | `touch .github/workflows/.gitkeep && git add -A && git commit -m "chore: trigger" && git push` |
| 切换分支 | `git branch -m master main && git push -u origin main` |

### 已知案例

- **posthog-design**: `gh workflow run` 返回 404，dummy commit 后成功
- **thunderbolt-design**: `gh workflow run` 返回 404，切换 main 分支后成功

---

## Pitfall 9: GitHub Pages API 返回 409 "already enabled" = 成功

### 症状

```bash
curl -X POST .../pages -d '{"build_type":"workflow"}'
# {
"message":"GitHub Pages is already enabled.",
"status":"409"}
```

### 含义

**409 = Pages 已经正确配置，无需任何操作。**

### 正确处理

```python
if response.status_code == 409:
    print("Pages already enabled — skip")  # 不重试，不报错
elif response.status_code == 201:
    print("Pages configured successfully")
```

### 验证

```bash
curl -s "https://api.github.com/repos/Owner/repo/pages" | jq '{url, build_type, source}'
```

### 已知案例

- **posthog-design**: 409 → Pages 正常工作（HTTP 200）
- **thunderbolt-design**: 409 → Pages 正常工作（HTTP 200）

---

## Pitfall 10: workflow_dispatch REST API 端点是 `/dispatches`（复数），不是 `/dispatch`

### 症状

```python
# ❌ 错误端点（singular /dispatch）
POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatch
# → 404 Not Found

# ✅ 正确端点（plural /dispatches）
POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatches
# → 204 No Content (success)
```

### 根因

GitHub REST API 的 workflow dispatch 端点是 **plural**：`/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches`（注意末尾的 `s`）。使用 singular `/dispatch` 会返回 404 Not Found。

### 正确调用

```python
# REST API — workflow_dispatch（手动触发）
# 端点必须是 /dispatches（复数）
dispatch_req = urllib.request.Request(
    f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{workflow_id}/dispatches",
    data=json.dumps({"ref": "main"}).encode(),
    headers={**HEADERS, "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(dispatch_req, timeout=15) as resp:
    print(f"Dispatch: {resp.status}")  # 204 = success
```

### 已知案例

- **shannon-design**: 用 singular `/dispatch` 返回 404，换成 `/dispatches` 后成功触发

---

## Pitfall 11: 首次 workflow 失败后，Pages API 需要重新 enable

### 症状

第一次 workflow 运行失败（Setup Pages 步骤失败），Pages 配置虽然创建了但 workflow 未完成构建。

之后即使 re-run failed jobs，Pages 可能仍处于未完成状态。

### 根因

GitHub Pages API 启用 `build_type: workflow` 后，需要等待第一次 workflow 成功完成，Pages 才能正确 serve 内容。如果第一次 workflow 失败，后续 re-run 成功后 Pages 才能正常。

### 解决

1. 确认 Pages API 配置存在（`build_type: workflow`）
2. 确保 workflow 已经成功完成（all steps success，conclusion=success）
3. 如果 workflow 已成功但 Pages 仍 404，尝试：
   - 等待 2-3 分钟（Pages 传播延迟）
   - 或手动 POST 重新触发 Pages build：`curl -X POST https://api.github.com/repos/{owner}/{repo}/pages/builds`

### 已知案例

- **shannon-design**: 第一次 workflow "Setup Pages" 失败，re-run 后成功，Pages 正常工作

---

## Pitfall 12: REST API 推送后文件散落在根目录而非子目录

### 症状

workflow 报错 `No such file or directory './docs-site'`，但 workflow YAML 中明确写了 `working-directory: ./docs-site`。

### 根因

REST API `PUT /repos/{owner}/{repo}/contents/{path}` 中的 `path` 参数决定了文件在仓库中的位置。如果推送时 path 写的是 `package.json` 而不是 `docs-site/package.json`，文件会出现在根目录而非 `docs-site/` 子目录。

### 验证

```python
GET /repos/{owner}/{repo}/git/trees/main?recursive=1
# 检查文件路径：
# ✅ 正确：docs-site/.vitepress/config.mjs 存在
# ❌ 错误：只有 .vitepress/config.mjs（散落在根目录）
```

### 解决

确保所有文件 path 都有正确的子目录前缀：
```python
# ✅ 正确
api_put(f"docs-site/package.json", content)
api_put(f"docs-site/.vitepress/config.mjs", content)
api_put(".github/workflows/vitepress-pages.yml", content)  # .github 在根目录是对的

# ❌ 错误（文件会散落在根目录）
api_put("package.json", content)
api_put(".vitepress/config.mjs", content)
```

### 已知案例

- **media-crawler-design**: path 前缀缺失导致 docs-site/ 不存在
- **multica-design**: 最初文件推到 docs-site/ 子目录，但 clone 后发现实际在根目录

---

## Pitfall 13: YAML frontmatter 值中含冒号未加引号导致 VitePress 构建失败

### 症状

```
[vitepress] incomplete explicit mapping pair; a key node is missed;
or followed by a non-tabulated empty line at line 37, column 30:
    details: 12+ integrations: Telegram, Discord, Slack, Feis ...
                             ^
file: /docs-site/index.md
```

### 根因

YAML 中 `key: value with : colon` 的 `value` 含有冒号时，YAML 解析器把第二个 `:` 视为新映射的开始，导致语法错误。

### 受影响场景

- frontmatter features 列表的 `details:` 字段（多集成平台描述）
- 任何 YAML 键值对的值中包含 URL 或多标签描述

### 修复

将含冒号的值用双引号包裹：

```yaml
# ❌ 错误
details: 12+ integrations: Telegram, Discord, Slack, Feishu, WeChat, and more.

# ✅ 正确
details: "12+ integrations: Telegram, Discord, Slack, Feishu, WeChat, and more."
```

### 验证

```bash
grep -rn "details:.*:" docs-site/
```

### 已知案例

- **nanobot-design**: `details: 12+ integrations: Telegram...` 缺失引号，25+ 次 CI 失败

---

## Pitfall 14: Git push 到 master 但 workflow 监听 main — 导致 CI 从不运行新代码

### 症状

- workflow 状态全是 `failure`，但 `gh run list` 显示所有 run 的 head_sha 都相同（旧 commit）
- `curl -sI https://yeluo45.github.io/repo/` 返回 404
- `gh workflow run` 触发后仍是旧 SHA 在跑
- `git log --oneline` 显示本地已更新，但 GitHub 上 contents API 返回的文件 SHA 还是旧的

### 根因

创建仓库时本地用 `git init`（默认 master），REST API 创建的 GitHub 默认分支是 `main`。push 到 master 但 workflow 的 `on: push: branches: [main]` 不匹配，workflow 监听的是 `main` 分支而非 master。

**关键症状**：`gh api repos/Owner/repo/branches` 显示 master 和 main 是两个不同的分支，且两者的 commit SHA 不一致。

### 诊断命令

```bash
# 检查所有分支的 SHA
gh api repos/Owner/repo/branches | jq '.[] | "\(.name) -> \(.commit.sha[0:7])"'

# 对比 GitHub ref SHA vs contents SHA
gh api repos/Owner/repo/git/refs/heads/main    # workflow 监听分支
gh api repos/Owner/repo/git/refs/heads/master # push 目标分支
gh api repos/Owner/repo/contents/docs-site/index.md | jq '.sha'  # 文件实际 SHA

# 如果 ref SHA 和 contents SHA 不一致 → 双分支问题
```

### 修复

强制将 workflow 监听的分支（main）指向最新 commit：

```bash
# 获取本地最新 commit SHA
git rev-parse HEAD

# 通过 gh api 强制更新 main ref
gh api -X PATCH -H "Content-Type: application/json" \
  --input <(echo "{\"sha\":\"$(git rev-parse HEAD)\",\"force\":true}") \
  /repos/Owner/repo/git/refs/heads/main
```

### 预防

1. 创建仓库前确认默认分支名称，或通过 API 创建时指定 `default_branch: "master"`
2. REST API 创建仓库后立即检查 `git/refs/heads` 确认实际分支名
3. 在 `git init` 后立即 `git branch -m main` 再开始工作，保持与 GitHub 默认一致

### 已知案例

- **nanobot-design**: 25+ 次 workflow 失败，根因是 push 到 master 而 workflow 监听 main

---

## Pitfall 15: Workflow Build 失败但日志被吞 — CI 调试方法论

### 症状

```
X Build
  ✓ Checkout
  ✓ Setup Pages
  ✓ Setup Node
  X Build
  - Upload artifact (skipped)
  - Deploy to GitHub Pages (skipped)
```

Build 步骤失败，但 `gh run view` 不显示具体错误信息，只显示步骤名。

### 根因

GitHub Actions 默认只显示步骤名，不显示步骤内的 stdout/stderr。如果不在 workflow 里主动捕获，构建失败的具体原因永远看不到。

### 正确调试步骤

**第一步：捕获构建输出到文件**

```yaml
- name: Build
  working-directory: ./docs-site
  run: |
    pnpm run build > ../vitepress-build.log 2>&1 || true
    echo "=== Build exit code: $? ==="
    cat ../vitepress-build.log
    echo "=== End of log ==="
    if [ ! -d ".vitepress/dist" ]; then
      echo "ERROR: .vitepress/dist was NOT created"
      exit 1
    fi
```

**第二步：查看失败步骤的完整日志**

```bash
gh run view <run-id> --log-failed 2>&1 | tail -60
```

**第三步：通过 contents API 验证 GitHub 上的文件是否已更新**

```bash
# 如果本地 SHA 和 GitHub SHA 不一致，说明 push 没有真正生效
gh api repos/Owner/repo/contents/docs-site/index.md | jq '{name, sha}'
git rev-parse HEAD  # 对比两者
```

### 教训

> 调试 CI 时，第一步永远是**让 CI 把日志写出来**，而不是猜错误原因。nanobot-design 白白失败了 25+ 次，因为没有人捕获 vitepress 的构建输出。第一个 diagnostic workflow commit 就暴露了 YAML 语法错误。

---

## 验证清单（新项目创建后）

- [ ] `theme/index.js` 使用 `extends DefaultTheme`，不是 `defineConfig`
- [ ] workflow YAML 没有 `environment:` 块
- [ ] GitHub Pages 已通过 API 启用 `build_type: workflow`
- [ ] `.github/workflows/` 目录下没有子目录
- [ ] 首次 push 后检查 workflow 运行状态
- [ ] 如 workflow 未自动触发，手动 POST `/actions/workflows/{id}/dispatches`（注意复数）
- [ ] **本地 npm install 使用 `--prefer-offline`**
- [ ] **workflow 中使用 `actions/cache` + `NPM_CONFIG_REGISTRY` + `prefer-offline`**
- [ ] **nav/sidebar 中的 link 值与实际文件名完全匹配**
- [ ] **启用 `ignoreDeadLinks: true`**
- [ ] **YAML frontmatter 中含冒号的值必须加双引号**
- [ ] **REST API 创建仓库后确认默认分支名称，确保本地分支和 workflow 监听分支一致**
- [ ] **CI 构建失败时必须捕获 stdout/stderr 到文件，防止日志被吞**
- [ ] 部署后 curl 验证 HTTP 200
