---
name: design-web-workflow
description: Design项目（设计规范文档站）从规划到交付的标准化工作流程 — 适用于 trading-agent-design 等多模块设计文档项目
tags: [design, documentation, multi-agent, github-pages]
category: workflow
---

# Design-Web 工作手册

> 本手册沉淀自 trading-agent-design 项目的开发经验，用于指导后续 design 类项目的标准化建设。

---

## 1. 核心设计理念

### 1.1 什么是 Design 项目

Design 项目是将复杂系统的设计规范文档化，并通过 Web 站点对外展示的文档工程。核心特征：

| 特征 | 说明 |
|------|------|
| 多模块 | 每个核心模块独立文档，如架构、数据源、策略等 |
| 可视化 | 通过 Web 站点渲染，比 Markdown 更易读 |
| 可交互 | 支持文档导航、搜索、版本切换 |
| 可演进 | 文档与实现同步，版本化管理 |

### 1.2 Design 项目的价值

```
原始需求 → 设计规范 → 文档站 → 协作沟通 + 知识沉淀
```

- **对团队**：统一设计语言，减少沟通成本
- **对项目**：设计决策可追溯，迭代有据可查
- **对外部**：展示技术实力，降低接入门槛

### 1.3 核心技术选型

| 层级 | 选型 | 原因 |
|------|------|------|
| 文档格式 | Markdown | 易于编写、结构清晰 |
| 渲染引擎 | **VitePress** | Vue 3 + Vite，默认支持 home layout、features、nav，官方推荐 |
| 样式框架 | VitePress CSS 变量 + custom.css | 通过 `.vitepress/theme/custom.css` 注入自定义样式 |
| 部署方式 | GitHub Pages (workflow mode) | Settings → Pages → Source: GitHub Actions |

> **实际项目参考**：astrbot-design 使用 VitePress，与本手册描述的 marked.js + Tailwind CSS 方案不同。VitePress 是 Vite 生态下的文档框架，功能更完整，推荐作为 Design 项目的默认选择。

### 1.4 多智能体协作模式

trading-agent-design 采用 13 Agent 分工协作，Design 项目可借鉴其**分层协作**思路：

```
设计决策层（Manager Agents）
    ↓
模块设计层（Specialist Agents） — 各自负责一个模块
    ↓
文档编写层（Executor） — 将设计文档 Markdown 化
    ↓
前端渲染层（Web） — 将 Markdown 渲染为可交互站点
```

---

## 2. 项目结构规范

### 2.1 目录结构

```
{project-name}/
├── README.md                    # 项目导航索引
├── SPEC.md                      # 主规范文档（项目概览）
├── index.html                   # 单页应用入口
├── package.json                 # 依赖
├── src/
│   └── main.js                  # 渲染逻辑
├── docs/                        # 纯文档（非构建产物）
│   ├── architecture.md
│   ├── data-source.md
│   └── ...
├── dist/                        # 构建产物（部署到 gh-pages）
│   ├── index.html
│   └── assets/
│       └── index-*.js
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions 部署配置
└── .gitignore
```

### 2.2 必选文档清单

| 文档 | 描述 | 状态要求 |
|------|------|----------|
| SPEC.md | 项目设计规范主文档 | 必须有 |
| README.md | 文档导航索引 | 必须有 |
| {module}.md | 各核心模块文档 | 按需 |
| index.html | Web 单页入口 | 必须有 |

### 2.3 模块划分原则

| 原则 | 说明 | 示例 |
|------|------|------|
| 单一职责 | 每个文档专注一个模块 | data-source-architecture.md 只讲数据源 |
| 层次清晰 | 按架构层次组织 | 架构层 → 模块层 → 实现层 |
| 索引导向 | README.md 导航所有文档 | 链接到每个模块文档 |
| API 优先 | 每个模块提供 API 接口规范 | 便于后续对接实现 |

---

## 3. 文档编写规范

### 3.1 文档头部元信息

每个模块文档必须包含：

```markdown
# Module Name

> 模块一句话描述

## 1. Overview
模块详细介绍

## 2. Architecture
架构图或流程图

## 3. API Reference
接口规范

## 4. Implementation Notes
已知约束和限制
```

### 3.2 图表规范

| 类型 | 格式 | 说明 |
|------|------|------|
| 架构图 | ASCII 图或 Mermaid | 文本即可，便于维护 |
| 流程图 | Mermaid | 支持动态渲染 |
| 时序图 | Mermaid | 用于 API 调用流程 |
| 数据结构 | Python dataclass 或 JSON | 便于程序理解 |

### 3.3 代码块规范

```markdown
```python
# 语言标识必须正确
class Example:
    pass
```

```yaml
# 配置文件示例
key: value
```

```sql
-- 数据库 schema
SELECT * FROM table
```
```

### 3.4 表格规范

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

---

## 4. Web 展示技术方案

### 4.1 推荐方案：VitePress

VitePress 是 Vue 官方文档框架，**推荐作为 Design 项目的默认选择**，内置 home layout、features、nav、sidebar、search。

### 4.2 VitePress 项目结构

```
docs-site/                      # 文档站点根目录
├── .vitepress/
│   ├── config.mjs              # VitePress 配置
│   ├── theme/
│   │   ├── index.js            # 主题入口（extends DefaultTheme）
│   │   └── custom.css          # 自定义样式
│   ├── public/                 # 静态资源源目录
│   │   └── astrbot_banner.png
│   └── dist/                   # 构建产物（GitHub Pages 部署）
├── index.md                    # 首页 Markdown
├── architecture.md             # 模块文档
└── package.json
```

**⚠️ 重要教训**：`public/` 目录中的文件**不会**在 `vitepress build` 时自动复制到 `dist/`。必须手动执行：
```bash
cp docs-site/.vitepress/public/astrbot_banner.png docs-site/.vitepress/dist/
```
验证方式：
```bash
# 检查 dist 中是否存在图片
ls docs-site/.vitepress/dist/*.png

# 检查 index.html 是否引用了图片路径
grep "astrbot_banner" docs-site/.vitepress/dist/index.html
```

> `public/` 的"自动复制"行为只在 `vitepress dev`（开发服务器）时通过 URL serve 实现，**build 时不会复制**，这是与 Hugo/Jekyll 等框架的关键区别。

**静态资源正确路径**：VitePress build 后，所有 public 资源引用路径为 `/astrbot_banner.png`（相对于站点根），但文件必须存在于 `dist/` 目录中。GitHub Actions workflow mode 部署时上传的是整个 `dist/` 目录，所以手动 cp 是必要的。

### 4.3 VitePress home layout frontmatter 示例

```markdown
---
layout: home

hero:
  name: "Project Name"
  text: "项目描述副标题"
  tagline: "基于 XXX 开源项目"
  image:
    src: /astrbot_banner.png
    alt: Banner Image
  actions:
    - theme: brand
      text: 架构分析
      link: /architecture
    - theme: brand
      text: 扩展方向
      link: /extension-directions

features:
  - icon: 🏗️
    title: 架构分析
    details: 9个核心模块、4种设计模式
    link: /architecture
    linkText: 查看文档
  # ... 任意数量
---
```

### 4.4 自定义主题样式（custom.css）

```css
/* 深紫蓝渐变 Hero 背景 */
.VPHome {
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  padding: 2rem 0;
}

/* 标题渐变色文字 */
.VPHero .name {
  font-size: 3.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Feature 卡片 hover 效果 */
.VPFeature {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  transition: all 0.3s ease !important;
}
.VPFeature:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(102, 126, 234, 0.5) !important;
  transform: translateY(-4px) !important;
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.15) !important;
}

/* Navbar 毛玻璃效果 */
.VPNav {
  background: rgba(15, 12, 41, 0.9) !important;
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

/* 按钮渐变 */
.VPButton.medium.brand {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}
.VPButton.medium.brand:hover {
  background: linear-gradient(135deg, #7c8ffa 0%, #8a5db5 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35);
}
```

### 4.5 VitePress 构建与部署

```bash
cd docs-site
pnpm install          # 首次安装依赖
pnpm run build        # 构建生产版本（输出到 .vitepress/dist）
pnpm run dev          # 本地开发预览（热重载）
```

GitHub Actions workflow mode 部署（推荐）：
```yaml
- name: Build
  working-directory: ./docs-site
  run: pnpm run build
- name: Upload artifact
  uses: actions/upload-pages-artifact@v3
  with:
    path: ./docs-site/.vitepress/dist
```

> **教训**：VitePress 构建产物中图片等静态资源在 `dist/` 根目录，不在 `dist/assets/`。验证方式：检查 `dist/index.html` 中图片路径是否为 `/astrbot_banner.png`，且该文件存在于 `dist/` 目录。

### 4.6 config.mjs 关键配置

```js
import { defineConfig } from "vitepress";

export default defineConfig({
  title: "Project Name",
  description: "项目描述",

  head: [
    ["link", { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
  ],

  themeConfig: {
    logo: "/astrbot_banner.png",   // 导航栏 logo（相对于 public 目录）

    nav: [
      { text: "Home", link: "/" },
      { text: "Architecture", link: "/architecture" },
      // ...
    ],

    sidebar: [{
      text: "Documentation",
      items: [
        { text: "Home", link: "/" },
        { text: "架构分析", link: "/architecture" },
        // ...
      ],
    }],

    socialLinks: [
      { icon: "github", link: "https://github.com/owner/repo" }
    ],

    footer: {
      message: "基于 XXX 开源项目构建",
      copyright: "Copyright © 2024-present XXX Contributors"
    },
  },
});
```

### 4.7 遗留方案：marked.js + Tailwind（不推荐）

<details>
<summary>点击展开旧方案（仅作参考）</summary>

```
index.html (入口)
    ↓
marked.js (Markdown → HTML)
    ↓
Tailwind CSS (样式)
    ↓
文档内容渲染
```

此方案适用于简单文档站，VitePress 可提供更完整的文档功能。

#### 4.7.1 暗色模式实现（CSP 变量方案）

当使用 Tailwind CDN 或无法使用 VitePress 内置暗色模式时，通过 CSS 变量实现：

**Step 1：HTML head 中定义 CSS 变量**

```html
<style>
  :root {
    --bg-primary: #ffffff;
    --bg-secondary: #f9fafb;
    --text-primary: #111827;
    --text-secondary: #374151;
    --border-color: #e5e7eb;
    /* ... 更多变量 */
  }
  html.dark {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --text-primary: #f1f5f9;
    --text-secondary: #cbd5e1;
    --border-color: #334155;
    /* ... 深色变量 */
  }
  body {
    background: var(--bg-primary);
    color: var(--text-primary);
    transition: background 0.2s, color 0.2s;
  }
  .card { background: var(--bg-secondary); border: 1px solid var(--border-color); }
  .nav-link { color: var(--text-secondary); }
  .nav-link:hover { background: var(--nav-hover); }
  .nav-link.active { background: var(--accent-bg); color: var(--accent-text); }
  .text-muted { color: var(--text-muted); }
  .text-primary { color: var(--text-primary); }
  .text-secondary { color: var(--text-secondary); }
</style>
```

**Step 2：JavaScript 中控制主题**

```javascript
// 初始化检测（系统偏好 + localStorage）
(function initDark() {
  const stored = localStorage.getItem('darkMode');
  if (stored === 'true' ||
      (stored === null && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  }
})();

// 切换函数
function toggleDark() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('darkMode', isDark);
  render(); // 重新渲染（更新图标等）
}
```

**Step 3：渲染函数中使用变量**

```javascript
// 首页渲染片段
app.innerHTML = `
  <aside class="aside w-64 border-r fixed h-full">
    <div class="flex items-center justify-between">
      <h1>🤖 TradingAgents</h1>
      <button id="themeToggle" onclick="toggleDark()">
        ${isDark ? '☀️' : '🌙'}
      </button>
    </div>
    <nav>
      <a class="nav-link ...">首页</a>
    </nav>
  </aside>
  <main class="card rounded-xl p-6 ...">
    <h2 class="text-primary">标题</h2>
    <p class="text-secondary">描述</p>
  </main>
`;
```

**Step 4：Tailwind 与 CSS 变量混用注意事项**

- Tailwind CDN（`script src="tailwindcss.com"`）不读取 VitePress 那样读取 `html.dark` class
- 纯 CSS 变量方案：所有颜色通过 `var(--xxx)` 变量引用，Tailwind 类只用于布局（`flex`、`w-64`等）
- **不要在 `<body>` 上使用 Tailwind 颜色类**（如 `class="bg-gray-50 text-gray-900"`），这会覆盖 CSS 变量，改用内联 style 或 CSS 类

**Step 5：Vite base 配置（子目录部署必读）**

当 SPA 部署在 GitHub Pages 子目录时，必须配置 `vite.config.js` 的 `base`：

```js
// vite.config.js
module.exports = {
  base: '/trading-agents-design/',
};
```

否则构建产物中的 asset 路径为 `/assets/index-xxx.js`（绝对路径），而实际部署在 `/trading-agents-design/assets/`，导致 404。

</details>

---

## 5. 子目录部署路径问题（重要教训）

**问题**：GitHub Pages 部署在子目录（如 `/trading-agents-design/`）时，绝对路径 `/assets/...` 会 404。

**原因**：
- 构建产物路径：`/assets/index-xxx.js`
- 实际部署路径：`/trading-agents-design/assets/index-xxx.js`
- 浏览器请求：`yeluo45.github.io/assets/index-xxx.js` → 404（解析到仓库根而非子目录）

**解决方案**：

在 `vite.config.js` 中配置 `base` 为子目录路径：

```js
// vite.config.js（CJS 格式，CommonJS）
module.exports = {
  base: '/trading-agents-design/',
};
```

```js
// vite.config.js（ESM 格式，需要 package.json 设置 type: "module"）
import { defineConfig } from 'vite';
export default defineConfig({
  base: '/trading-agents-design/',
});
```

重新构建后，资源路径自动变为 `/trading-agents-design/assets/index-xxx.js`。

**修复流程**：
1. 添加/修改 `vite.config.js` 的 `base` 配置
2. `npm run build` 重新构建
3. 通过 REST API 更新 gh-pages 分支
4. 等待 GitHub Pages 重新部署

**验证方法**：
```bash
# 正确路径（正确）
curl -s "https://yeluo45.github.io/trading-agents-design/" | grep "index-xxx"
# 输出: src="/trading-agents-design/assets/index-xxx.js"

# 错误路径（绝对路径，404）
curl -s "https://yeluo45.github.io/trading-agents-design/" | grep "/assets/index"
# 输出: src="/assets/index-xxx.js"  ← 错误
```

**浏览器缓存问题**：
部署后浏览器可能仍缓存旧 HTML（带旧路径），表现为：
- `curl` 返回新路径（正确）
- 浏览器仍加载旧路径（404）

解决：强制刷新（Ctrl+Shift+R）或添加版本参数 `?v=2`

> **注意**：VitePress 构建的 `dist/index.html` 中资源路径已经是相对路径（相对于 `dist/` 目录），因此使用 workflow mode 部署到子目录时**不会出现此问题**，这是 VitePress 相比手写 marked.js 方案的另一个优势。

---

## 6. 非 Git 仓库处理

执行迭代前先检查目标目录是否为 Git 仓库：
```bash
git -C /path/to/project rev-parse --is-inside-work-tree 2>/dev/null || echo "not-git"
```

**非 Git 仓库的处理流程**：
1. 仍创建所有文档文件（SPEC.md、模块文档、index.html）
2. **跳过** git commit/push 步骤
3. 告知用户需要在 GitHub 创建仓库并启用 GitHub Pages 才能部署
4. GitHub Actions 配置文件（.github/workflows/）仍可创建，用户启用 Pages 后自动生效

**教训**：deepcode-design 项目已创建完整文档站，但因非 git 仓库无法提交。设计文档已就位，待项目上 GitHub 后即可部署。

---

## 7. 新仓库少文件上传：PUT /contents 而非 blob→tree→commit

对于**新仓库 + 少量文件（<10）**的场景，直接用 `PUT /repos/{owner}/{repo}/contents/{path}` 上传最简单，无需完整的 blob→tree→commit→ref 流程：

```bash
GH_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
OWNER=YeLuo45
REPO=new-design-repo

for file in README.md SPEC.md index.html; do
  CONTENT=$(base64 -w0 "$file" | tr -d '\n')
  curl -s -X PUT \
    -H "Authorization: token $GH_TOKEN" \
    -H "Content-Type: application/json" \
    https://api.github.com/repos/$OWNER/$REPO/contents/$file \
    -d "{\"message\":\"docs: add $file\",\"content\":\"$CONTENT\"}"
done
```

**条件**：
- 新仓库（无 commit 历史）
- 文件数量少（<10）
- 不需要保留目录结构（GitHub 自动创建父目录）

**复杂场景（大文件、多文件、有历史）**：回退到 `github-api-push-when-network-blocks-git` skill 的完整 blob→tree→commit→ref 流程。

---

## 8. GitHub Actions 部署配置

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
      - uses: actions/deploy-pages@v4
```

### 构建命令

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

---

## 9. GitHub Pages 子目录部署

### 9.1 部署模式

| 模式 | 适用场景 | 配置 |
|------|----------|------|
| workflow mode | 推荐，官方支持 | Settings → Pages → Source: GitHub Actions |
| gh-pages branch | 传统方式 | Settings → Pages → Source: gh-pages branch |

### 9.2 子目录访问

- URL 格式：`https://{username}.github.io/{repo-name}/`
- 访问验证：`curl -I https://{username}.github.io/{repo-name}/`
- 状态码 200 = 部署成功

### 9.3 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 404 | 路径错误 | 检查 index.html 资源路径 |
| 空白页 | JS 加载失败 | 检查控制台错误 |
| 样式错乱 | CSS 未加载 | 检查 Tailwind CDN 或构建产物 |

### 9.4 Git Push 超时时的 REST API 强制推送

当 `git push origin gh-pages` 超时（如网络阻塞），使用 GitHub REST API 绕过：

```bash
# 1. 获取 token（从 git-credentials）
TOKEN=$(grep github.com ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')

# 2. 获取当前文件 SHA
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref=gh-pages" | jq -r '.sha'

# 3. 用 curl PUT 更新文件
curl -X PUT -H "Authorization: token $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "fix: 修复路径",
       "content": "'"$(base64 -w0 dist/index.html)"'",
       "sha": "{file_sha}",
       "branch": "gh-pages"
     }' \
  "https://api.github.com/repos/{owner}/{repo}/contents/{path}"
```

**Python 等效实现**：
```python
import base64, subprocess, json, urllib.request

with open('/home/hermes/.git-credentials', 'r') as f:
    token = f.read().strip().split('\n')[0].split('://')[1].split('@')[0].split(':')[1]

repo = "owner/repo"
content_b64 = base64.b64encode(open('dist/index.html', 'rb').read()).decode()

# 先获取当前 SHA
req = urllib.request.Request(
    f"https://api.github.com/repos/{repo}/contents/index.html?ref=gh-pages",
    headers={"Authorization": f"token {token}"}
)
with urllib.request.urlopen(req) as resp:
    current_sha = json.loads(resp.read())['sha']

# PUT 更新
payload = json.dumps({
    "message": "fix: 修复路径",
    "content": content_b64,
    "sha": current_sha,
    "branch": "gh-pages"
}).encode()

req = urllib.request.Request(
    f"https://api.github.com/repos/{repo}/contents/index.html",
    data=payload,
    headers={"Authorization": f"token {token}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    print(f"Success: {result['commit']['sha']}")
```

**验证推送结果**：
```bash
curl -s "https://raw.githubusercontent.com/{owner}/{repo}/gh-pages/index.html" | grep 'src="assets/'
```

---

## 10. 维护流程

### 14.9 gh repo create 不要加 --source

加 `--source` 会导致 "Unable to add remote origin"。正确做法：

```bash
gh repo create yeluo45/repo --public  # 只创建空仓库
cd /path/to/local && git push -u origin master
```

### 14.10 pnpm workspace 会将 node_modules 跟踪进 git

`git ls-files | grep -c node_modules` 正常应为 0。若为 4000+，先清理再 push：

```bash
git rm -r --cached docs-site/node_modules
git add .gitignore && git commit -m "chore: remove node_modules"
```

### 14.11 git push 失败时的 REST API Fallback

网络阻塞（HTTP 408、GnuTLS EOF）导致 git push 超时时，用 Contents API 上传关键文件：

```bash
gh api --method PUT "repos/{owner}/{repo}/contents/{path}" \
  -f content="$(base64 -w0 file.md | tr -d '\n')" -f message="add file.md"
```

注意：更新已存在文件要先 GET 获取 sha，否则 422 "sha wasn't supplied"。详见 `references/git-push-lessons.md`。

### 14.12 批量 push 后验证清单

```bash
for repo in proj-a proj-b; do
  count=$(curl -s --max-time 10 \
    "https://api.github.com/repos/yeluo45/$repo/contents/" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null)
  echo "$repo: $count entries"
done
```

## 15. 常用模块文档列表

```
修改 Markdown → 本地预览 → 提交 PR → 合并 main → GitHub Actions 自动部署
```

### 10.2 版本管理

| 类型 | 管理方式 | 示例 |
|------|----------|------|
| 项目版本 | SPEC.md 头部 | Version: cn-0.1.15 → cn-0.1.16 |
| 模板版本 | prompt-template-system.md | 语义版本 {major}.{minor}.{patch} |
| 文档版本 | Git commit | 每个 deliverable 单独 commit |

### 10.3 本地预览

```bash
# 安装依赖
npm install

# 开发模式（热重载）
npm run dev

# 构建生产版本
npm run build

# 本地预览构建结果
npm run preview
```

---

## 11. 设计理念总结

### 11.1 核心理念

| 理念 | 说明 |
|------|------|
| **模块化** | 每个设计决策独立文档，便于单独演进 |
| **可执行** | 文档包含 API 规范，可直接对接实现 |
| **可视化** | 架构图、流程图让设计更直观 |
| **可追溯** | 版本化管理，设计决策有据可查 |

### 11.2 与 Implement 项目的区别

| 维度 | Design 项目 | Implement 项目 |
|------|-------------|----------------|
| 产出物 | 文档 + Web 站点 | 可运行代码 |
| 验收标准 | 文档完整性、可读性 | 功能正确性、性能指标 |
| 版本粒度 | 按模块/按文档 | 按 feature |
| 生命周期 | 与项目共存，持久化 | 实现后交付，后续迭代 |

### 11.3 适用场景

✅ **适合 Design 项目的场景**：
- 复杂系统的架构设计
- 多模块协作的设计规范
- 需要对外展示的技术文档
- 团队协作的设计共识

❌ **不适合 Design 项目的场景**：
- 简单项目（直接 README.md 即可）
- 纯实现类项目（不需要设计文档）
- 快速原型验证（设计文档是负担）

---

## 12. 首页视觉优化（常见问题）

### 12.1 "页面太朴素"的调试路径

当用户反馈首页视觉不够好时，不要急于改动布局，先按以下顺序排查：

**Step 1：验证资源加载**
```bash
# 检查 CSS 是否包含自定义样式（通过颜色值验证）
curl -s "https://example.github.io/assets/style.Xxxx.css" | grep -c "linear-gradient\|VPHome"

# 检查图片是否可访问
curl -s -I "https://example.github.io/astrbot_banner.png" | head -1
```

**Step 2：分析实际 DOM 结构**
用浏览器开发者工具检查：
- Hero 区域是否正确渲染（`.VPHero` 存在）
- Features 卡片数量（`.VPFeature` 应有 N 个）
- 图片是否有 src 属性（非 broken）
- CSS 变量是否生效（检查 computed background）

**Step 3：常见视觉问题和根因**

| 问题 | 可能原因 | 修复方向 |
|------|----------|----------|
| 渐变背景不显示 | custom.css 未被 VitePress 加载 | 确认 theme/index.js 正确 import custom.css |
| 图片不显示 | public 目录资源未 cp 到 dist | 手动复制到 dist/ |
| Feature 卡片挤成一列 | 正常（移动端响应式） | 检查桌面端宽度是否正常 |
| 颜色单调/无层次 | 渐变色不够深或对比度不够 | 调整 CSS 变量加深背景/加强渐变 |
| 视觉太平 | 缺少阴影/光晕/边框 | 添加 decorative glow orb、card shadow |

**Step 4：迭代改进的 CSS 策略**

```css
/* 1. 背景：多层渐变 + 装饰性光晕 */
.VPHome {
  background: linear-gradient(160deg, #0a0a1a 0%, #14143c 40%, #1a1035 70%, #0f0c29 100%) !important;
}
.VPHome::before {
  content: '';
  position: absolute;
  top: -120px; left: -100px;
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(102,126,234,0.18) 0%, transparent 70%);
  pointer-events: none; z-index: 0;
}

/* 2. Hero：文字渐变色 + 图片圆角边框 */
.VPHero .name {
  background: linear-gradient(120deg, #667eea 0%, #764ba2 40%, #f093fb 80%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
}
.VPHero .image-container {
  border-radius: 16px !important;
  border: 1px solid rgba(102,126,234,0.2) !important;
  box-shadow: 0 24px 64px rgba(102,126,234,0.2) !important;
}

/* 3. Feature 卡片：hover 上浮 + 阴影 */
.VPFeatures .grid-6:hover {
  transform: translateY(-5px) !important;
  box-shadow: 0 16px 48px rgba(102,126,234,0.18) !important;
}

/* 4. Navbar：玻璃拟态 */
.VPNav {
  background: rgba(10,10,26,0.88) !important;
  backdrop-filter: blur(16px) saturate(180%) !important;
  border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}
```

### 12.2 Features 数量与布局的关系

- **6 个以内**：grid-6 每行 3 列（桌面端），视觉疏朗
- **8-9 个**：grid-6 每行 3 列，卡片变小，适合密集展示
- **10+ 个**：考虑分两行，或去掉 features 直接用文档列表

 astrbot-design 最终用 8 个（删掉了重复的"快速开始"），效果较好。

### 12.3 构建后必须验证的文件

```bash
# 1. dist 中有图片
ls dist/*.png

# 2. index.html 引用了图片
grep "astrbot_banner" dist/index.html

# 3. CSS 中有自定义样式
grep -c "linear-gradient\|VPHome" dist/assets/style.*.css

# 4. 所有 JS/CSS 文件存在（无 404）
grep -o 'src="/assets/[^"]*"' dist/index.html | while read f; do
  path="${f#src=\"}; path="${path%\"}"
  curl -s -o /dev/null -w "%{http_code}" "https://example.github.io$path"
done
```

---

## 13. 快速开始 Checklist

### 12.1 新建 VitePress Design 项目

- [ ] 确定项目名称和定位
- [ ] 创建 GitHub 仓库
- [ ] 初始化 `docs-site/` 目录结构
- [ ] 配置 `.vitepress/config.mjs`
- [ ] 配置 `.vitepress/theme/index.js` + `custom.css`
- [ ] 放置静态资源到 `.vitepress/public/`
- [ ] 配置 `.github/workflows/deploy.yml`（workflow mode）
- [ ] 创建首页 `index.md`（layout: home + features）
- [ ] 创建模块文档 Markdown
- [ ] 本地 `pnpm run dev` 预览
- [ ] `pnpm run build` 确认 dist 正确
- [ ] `git init` + `git add -A` + `git commit` 初始化仓库
- [ ] **`git remote add origin https://github.com/yeluo45/{project-name}.git`** 添加远程仓库（用 set-url 如果已存在）
- [ ] **README.md 添加 `**GitHub Repository**: https://github.com/yeluo45/{project-name}` 行**
- [ ] `git add -A && git commit` 提交 README 更新（单独 commit）
- [ ] 提交并 push，验证 GitHub Pages 部署

### 12.2 添加新模块文档

- [ ] 确定模块名称和范围
- [ ] 编写模块 Markdown（放入 docs-site/ 根目录）
- [ ] 更新 `config.mjs` 的 nav 和 sidebar
- [ ] 本地预览验证
- [ ] 提交并部署

---

## 15. pnpm workspace 与 node_modules 被 git 跟踪问题

### 问题

pnpm workspace 会在 `docs-site/node_modules/.pnpm/` 下创建大量包的符号链接，`git ls-files` 会将其全部跟踪进来：

```bash
git ls-files | grep -c node_modules
# → 4912  ← 错误：应该为 0
```

### 解决

```bash
git rm -r --cached docs-site/node_modules
echo "node_modules/" >> .gitignore
git add .gitignore && git commit -m "chore: remove node_modules from tracking"
```

验证：`git ls-files | grep -c node_modules` 应返回 0。

### 预防

在项目 `.gitignore` 中确保包含：
```
node_modules/
```

## 16. GitHub Actions workflow mode 的验证与触发

### 验证构建状态

```bash
gh run list --repo yeluo45/{repo} --limit 5
```

### 手动触发 workflow

如果 push 后 GitHub Pages 未开始部署：

```bash
gh api --method POST "repos/yeluo45/{repo}/actions/workflows/deploy.yml/dispatches" \
  -f ref="main"
# → 204 No Content = 成功
```

## 17. 快速检查清单（push 后验证）

```bash
# 1. 检查所有仓库文件数
for repo in generic-agent-design open-space-design scrapling-design \
            claude-code-design claudecodesrc-design freqtrade-develop-design \
            langcli-design ohmypi-design opencode-dev-design ruflo-design; do
  count=$(curl -s --max-time 8 \
    "https://api.github.com/repos/yeluo45/$repo/contents/" | \
    grep -c '"name"' || echo 0)
  echo "$repo: $count entries"
done

# 2. 检查 GitHub Pages 部署状态（等 2-3 分钟后）
for repo in generic-agent-design open-space-design; do
  status=$(curl -sI --max-time 10 "https://yeluo45.github.io/$repo/" | head -1)
  echo "$repo: $status"
done
```

---

## 16. 参考资料

- VitePress 官方文档：https://vitepress.dev/
- VitePress GitHub：https://github.com/vuejs/vitepress
- trading-agent-design: https://yeluo45.github.io/trading-agents-design/
- astrbot-design: https://yeluo45.github.io/astrbot-design/
- GitHub Pages: https://pages.github.com/

## 14. 批量创建模式（多项目并行迭代）

当需要连续创建多个同类型 VitePress 设计文档站时（如开源项目源码分析系列），可按以下模式操作：

### 14.1 统一的主题配色规划

| 项目 | 源码 | 主题色 |
|------|------|--------|
| generic-agent-design | GenericAgent | 蓝紫色 |
| open-space-design | OpenSpace | 深蓝绿 |
| scrapling-design | Scrapling | 橙红色 |
| claude-code-design | claude-code | 紫色 |
| claudecodesrc-design | collection-claude-code-source-code | 橙黄色 |
| freqtrade-develop-design | freqtrade-develop | 绿色 |
| langcli-design | langcli | 蓝色 |
| ohmypi-design | oh-my-pi | 青绿色 |
| opencode-dev-design | opencode-dev | 紫色 |
| ruflo-design | ruflo | 琥珀色 |

每个项目使用不同的 `--vp-c-brand` 色值，形成视觉区分。

### 14.2 批量创建流程

```bash
# 1. 为每个项目创建目录结构
for project in generic-agent-design open-space-design scrapling-design claudecodesrc-design freqtrade-develop-design langcli-design; do
  mkdir -p /home/hermes/opensource/$project/docs-site/.vitepress/{theme,public}
done

# 2. 每个项目独立：package.json → config.mjs → theme → 内容文档 → 构建
# 3. 每个项目独立 git init + commit（每个项目单独执行，不要跨项目合并命令）
# 4. 每个项目添加远程仓库: git remote -v | grep -q "^origin" && git remote set-url origin https://github.com/yeluo45/{project}.git || git remote add origin https://github.com/yeluo45/{project}.git
# 5. 每个项目更新 README.md 添加 GitHub Repository 链接
# 6. 每个项目 commit README 更新
# 7. GitHub 创建仓库 + push + 启用 GitHub Actions
```

**⚠️ git init 顺序陷阱**：批量执行时，`git init` 必须在对应项目目录中单独运行，不能跨目录批量执行。如果前一个项目的 `git init` 输出被后续命令覆盖，可能导致部分项目未被初始化。正确做法：每个项目 `cd $dir && git init && git add -A && git commit` 作为独立步骤验证。

### 14.3 关键差异点（每个项目需单独配置）

- `config.mjs` 的 `title`、`base`（必须匹配仓库名）
- `custom.css` 的主题渐变色
- `deploy.yml` 的 `url: https://user.github.io/repo/`
- 首页 `index.md` 的项目名称和描述
- `package.json` 的 `name` 字段

### 14.4 内容文档结构（源码分析类项目通用模板）

常用模块文档：
- `core-modules.md` — 核心模块分析
- `tool-system.md` — 工具系统
- `slash-commands.md` — 斜杠命令
- `permission-system.md` — 权限系统
- `context-management.md` — 上下文管理
- `subprojects.md` — 子项目对比
- `api-providers.md` — API Providers
- `feature-flags.md` — Feature Flags
- `budget-mode.md` — 预算模式

---

## 15. Git 初始化教训（批量创建必读）

### 15.1 git init 不等于 git repo 存在

`git init` 在已有 `.git` 目录的目录中运行时：
- **exit code = 0**（不会报错）
- **不会重新初始化**
- **remote 不会更新**（如果已有 origin）

验证正确方式：
```bash
# 先验证 git repo 是否真实存在
git rev-parse --git-dir 2>/dev/null && echo "git repo exists" || echo "not a git repo"
```

### 15.2 git remote add 的安全做法

```bash
# 错误：如果 origin 已存在会 fatal
git remote add origin https://github.com/user/repo.git

# 正确：用 set-url 或先检查
git remote -v | grep -q "^origin" && git remote set-url origin URL || git remote add origin URL
```

### 15.3 批量 git init 隔离性

每个项目必须单独执行 git init，不能跨项目批量：
```bash
# 正确：每个项目单独 git init
cd /path/to/project-a && git init && git add -A && git commit
cd /path/to/project-b && git init && git add -A && git commit

# 错误：期望在子目录中执行但实际在父目录运行
cd /path/to && git init project-a  # 这不会进入 project-a
```

### 15.4 README.md 必须包含 GitHub Repository 链接

每个 design 项目 README.md 应在标题后、Project Structure 前添加：

```markdown
# Project Name

Design documentation site for [SourceRepo](https://github.com/owner/source) — description.

**GitHub Repository**: https://github.com/yeluo45/project-name
```

这应该作为**单独的 commit**，不要与初始 commit 合并。

### 15.5 批量创建后的检查清单

对每个新创建的项目验证：
- [ ] `git rev-parse --git-dir` 返回 `.git` 路径
- [ ] `git remote -v` 显示正确的 origin URL
- [ ] README.md 包含 GitHub Repository 链接
- [ ] `pnpm run build` 成功（exit 0）
- [ ] `.vitepress/dist/index.html` 存在

## 16. REST API 推送路径映射陷阱（media-crawler-design 教训 2026-05-15）

> 通过 REST API `PUT /repos/{owner}/{repo}/contents/{path}` 推送文件到新仓库时，`path` 参数直接决定文件在仓库中的存放位置。

### 16.1 根因

```python
# ❌ 错误：path 只写文件名 → 文件出现在 repo 根目录
api_put(".github/workflows/vitepress-pages.yml", content, "add workflow")
# 结果：.github/workflows/ 在 repo 根目录（不在 docs-site/ 内）

# ✅ 正确：path 加子目录前缀
api_put(f"docs-site/.github/workflows/vitepress-pages.yml", content, "add workflow")
# 结果：.github/workflows/ 在 docs-site/ 子目录内
```

**症状**：workflow 文件跑到 `repo/.github/workflows/vitepress-pages.yml`，但 `docs-site/` 目录为空。GitHub Actions 找不到 workflow。

**验证**：
```bash
# 检查 repo 根目录是否有 .github/
GET /repos/{owner}/{repo}/contents/.github

# 检查 docs-site/ 是否存在
GET /repos/{owner}/{repo}/contents/docs-site

# 检查 workflow 文件实际位置
GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1
# 搜索 ".github/workflows" 出现在哪一层
```

### 16.2 Workflow 文件必须放在 Repo Root（claude-howto-design 教训 2026-05-15）

**症状**：workflow 文件在 `docs-site/.github/workflows/vitepress-pages.yml`，GitHub Actions 报：
```
Workflow does not exist or is disabled
```

**根因**：GitHub Actions 的 workflow 文件必须在 repo root 的 `.github/workflows/`，不能嵌套在子目录。

**正确目录结构**：
```
repo/
├── docs-site/
│   ├── .vitepress/
│   │   └── dist/          # 构建产物
│   ├── index.md
│   └── package.json
└── .github/
    └── workflows/
        └── vitepress-pages.yml    # ← repo root，不是 docs-site/.github/
```

**两种模式的 artifact path**：

| 模式 | workflow 位置 | artifact path |
|------|--------------|---------------|
| workflow mode | `.github/workflows/` (repo root) | `.vitepress/dist` |
| gh-pages 模式 | `.github/workflows/` (repo root) | `docs-site/.vitepress/dist` |

**修复**：如果 workflow 已在错误位置，通过 REST API 移动：
```python
# 读取错误位置内容
content = get_file_sha("docs-site/.github/workflows/vitepress-pages.yml")
# 删掉错误位置
delete_file("docs-site/.github/workflows/vitepress-pages.yml")
# 写到正确位置
api_put(".github/workflows/vitepress-pages.yml", content, "fix: move workflow to repo root")
```

### 16.3 REST API 创建新仓库后的 GitHub Pages 配置

```python
# 1. 启用 GitHub Pages（workflow mode，不需要 gh-pages 分支）
PUT /repos/YeLuo45/{repo}/pages
{"build_type": "workflow"}
# 成功返回 201

# 2. 触发首次 workflow dispatch
POST /repos/YeLuo45/{repo}/actions/workflows/vitepress-pages.yml/dispatches?ref=main
# 成功返回 204

# 3. 验证 Pages 配置
GET /repos/YeLuo45/{repo}/pages
# 返回 { "build_type": "workflow", "status": "queued" }
```

**常见错误**：新仓库用 `source.branch: "gh-pages"` → 422（分支不存在），必须用 `build_type: "workflow"`。

### 16.4 proposals.json 同步：新增 Design 项目的正确顺序

```python
# 1. 先更新 GitHub proposals.json
GET /repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json
# 获取 SHA

new_project = {
    "id": "PRJ-YYYYMMDD-XXX",
    "name": "project-name-design",
    "gitRepo": "https://github.com/NanmiCoder/SourceRepo",
    "localPath": "",
    "description": "项目描述",
    "proposalCount": 0,
    "lastUpdate": "YYYY-MM-DD",
    "proposals": []
}

PUT /repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json
{
  "message": "feat: add project-name-design",
  "content": <base64 of updated proposals.json>,
  "sha": <current_sha>
}

# 2. 同时更新本地 CSV
# projects.csv 和 proposals.csv 都要添加新行

# 3. 验证数量
# CSV data rows = GitHub projects count = boss 要求的项目总数
```
