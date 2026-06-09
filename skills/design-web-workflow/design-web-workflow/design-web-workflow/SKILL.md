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

### 4.5 VitePress 子目录部署：base 配置（重要）

当 VitePress 部署到 GitHub Pages 子目录（如 `https://user.github.io/repo-name/`）时，**必须**在 `config.mjs` 中设置 `base`，否则所有导航链接都指向仓库根路径导致 404。

```js
// .vitepress/config.mjs
export default defineConfig({
  title: "Project Name",
  base: "/repo-name/",   // ← 必须设置，结尾的 / 不能少
  themeConfig: {
    nav: [
      { text: "Home", link: "/" },
      { text: "Architecture", link: "/architecture" },   // 构建后 → /repo-name/architecture.html
    ],
    // ...
  },
});
```

**效果**：设置后所有链接自动加前缀 `/repo-name/`，导航链接、侧边栏、资源路径均正确。

**常见症状**：首页正常（`/` 解析到 `/repo-name/`），但点击导航链接跳转到 `/architecture.html`（404），原因就是缺少 `base` 配置。

**验证**：
```bash
# 检查构建产物中链接是否包含 base 前缀
grep -o 'href="/repo-name/[^"]*"' .vitepress/dist/index.html
# 正确输出: href="/repo-name/architecture.html"
# 错误输出: href="/architecture.html"  ← 缺少 base
```

---

### 4.6 public/ 目录不会自动复制到 dist（重要）

**问题**：VitePress 的 `public/` 目录在 `vitepress build` 时**不会**自动复制文件到 `dist/`。这与 Hugo/Jekyll 等框架不同。

**场景**：在 `public/` 放了一张图片 `astrbot_banner.png`，`config.mjs` 中 `logo: "/astrbot_banner.png"`，但构建后 `dist/astrbot_banner.png` 不存在，图片 404。

**解决**：构建后手动复制：
```bash
cp docs-site/.vitepress/public/astrbot_banner.png docs-site/.vitepress/dist/
```

**验证**：
```bash
# 检查 dist 中是否存在图片
ls docs-site/.vitepress/dist/astrbot_banner.png

# 检查 index.html 是否引用了图片
grep "astrbot_banner" docs-site/.vitepress/dist/index.html
```

**根本原因**：`public/` 在 `vitepress dev` 时通过开发服务器 URL 直接 serve，但 `build` 时 Vite 只处理 `theme/` 和 `dist/` 相关文件，public 目录的复制逻辑需要手动触发或通过构建钩子。

---

### 4.7 vp-icons.css 缺失问题

**症状**：构建后 `dist/vp-icons.css` 不存在，但 `index.html` 引用了它，导致样式缺失。

**原因**：某些 VitePress 版本构建时 `vp-icons.css` 未被正确输出。

**解决**：确认源目录有该文件：
```bash
ls docs-site/.vitepress/dist/vp-icons.css   # 检查是否存在
```

如果 dist 中缺失但 index.html 引用了它，检查 VitePress 版本，或在 `config.mjs` 中显式引入。

---

### 4.8 VitePress 构建与部署

```bash
cd docs-site
pnpm install          # 首次安装依赖
pnpm run build       # 构建生产版本（输出到 .vitepress/dist）
pnpm run dev         # 本地开发预览（热重载）
```

**部署检查清单**：
1. `config.mjs` 中已设置 `base: "/repo-name/"`
2. 构建后 `dist/` 中静态资源存在（手动 cp public/ 资源）
3. `dist/index.html` 中链接包含 base 前缀
4. GitHub Actions workflow 上传整个 `dist/` 目录

> **教训**：VitePress 构建产物中图片等静态资源在 `dist/` 根目录（不在 `dist/assets/`）。验证：`ls dist/*.png` 应有文件。

**GitHub Actions workflow mode 部署（workflow mode）**：
```yaml
- name: Build
  working-directory: ./docs-site
  run: pnpm run build
- name: Setup Pages
  uses: actions/configure-pages@v4
- name: Upload artifact
  uses: actions/upload-pages-artifact@v3
  with:
    path: ./docs-site/.vitepress/dist
- name: Deploy to GitHub Pages
  uses: actions/deploy-pages@v4
```

> **重要**：artifact path 必须填 `.vitepress/dist`（VitePress 的输出目录），不是 `dist`。

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

**问题**：GitHub Pages 部署在子目录（如 `/repo-name/`）时，绝对路径 `/assets/...` 会 404。

**原因**：
- 构建产物路径：`/assets/index-xxx.js`
- 实际部署路径：`/repo-name/assets/index-xxx.js`
- 浏览器请求：`user.github.io/assets/index-xxx.js` → 404

### 5.1 VitePress 解决方案（正确方式）

在 `.vitepress/config.mjs` 中设置 `base`：

```js
export default defineConfig({
  title: "Project Name",
  base: "/repo-name/",   // ← 必须，结尾 / 不能少
  themeConfig: {
    nav: [
      { text: "Home", link: "/" },
      { text: "Architecture", link: "/architecture" },
    ],
  },
});
```

重新构建后，所有资源路径自动变为 `/repo-name/assets/...`。

**验证**：
```bash
# 检查链接是否包含 base 前缀
grep -o 'href="/repo-name/[^"]*"' .vitepress/dist/index.html
```

### 5.2 旧方案：marked.js + vite.config.js（不适用于 VitePress）

<details>
<summary>点击展开（仅适用于手写 SPA 方案）</summary>

对于**手写 marked.js + Tailwind 的 SPA 方案**，需要在 `vite.config.js` 中配置 `base`：

```js
// vite.config.js（CJS）
module.exports = {
  base: '/repo-name/',
};
```

```js
// vite.config.js（ESM，需 package.json 设置 type: "module"）
import { defineConfig } from 'vite';
export default defineConfig({
  base: '/repo-name/',
});
```

</details>

**浏览器缓存问题**：部署后浏览器可能仍缓存旧 HTML（带旧路径），表现为 `curl` 返回新路径但浏览器 404。解决：强制刷新（Ctrl+Shift+R）。

> **注意**：VitePress 的 `base` 配置是针对 `config.mjs` 的，**不是** `vite.config.js`（VitePress 不使用项目根目录的 vite.config.js）。

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

### 10.1 文档更新流程

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
- [ ] 提交 git 并 push，验证 GitHub Pages 部署

### 12.2 添加新模块文档

- [ ] 确定模块名称和范围
- [ ] 编写模块 Markdown（放入 docs-site/ 根目录）
- [ ] 更新 `config.mjs` 的 nav 和 sidebar
- [ ] 本地预览验证
- [ ] 提交并部署

---

### 13.1 补充参考资料

- `references/subagent-parallel-and-github-api-push.md` — 子 Agent 并行执行技巧（batch size=3）、SHA-first PUT /contents 推送模式、GitHub Pages 手动触发构建、subagent 收尾清单
- `references/navigation-standardization.md` — 多页面文档站导航栏统一规范：标准 HTML/CSS 模式、一致性验证测试、subagent 导航交接检查清单。**重要**：并行生成多页面时必须使用此参考文件防止导航结构漂移

---

## 14. hermes-agent-design 项目经验（2026-05-13）

> 本节记录从 hermes-agent-design 项目沉淀的经验：VitePress + GitHub Actions workflow mode 文档站。

### 14.1 项目背景

hermes-agent-design 是纯设计文档站（无运行代码），初期使用手动维护的 HTML 文件（根目录 7 个 .html），后升级为 VitePress 自动构建。

### 14.2 双轨并行策略

hermes-agent-design 采用新旧系统并行：

| 层级 | 路径 | 说明 |
|------|------|------|
| 旧（手动 HTML） | 根目录 `*.html` | GitHub Pages 指向根目录 |
| 新（VitePress） | `docs-site/.vitepress/dist/` | GitHub Actions 自动构建 |

**策略**：新站点验证稳定后，再将 GitHub Pages 切换到 VitePress 构建产物。

### 14.3 VitePress 目录结构（docs-site）

```
docs-site/
├── .vitepress/
│   ├── config.mjs           # nav + sidebar + themeConfig
│   ├── theme/
│   │   ├── index.js         # extends DefaultTheme
│   │   └── style.css         # 自定义暗色主题 CSS
│   └── dist/                # 构建产物（GitHub Pages 部署路径）
├── index.md                 # layout: home（首页）
├── api.md
├── dashboard.md
├── mcp.md
├── agent-runner.md
├── platform-adapter.md
└── plugin-development.md
```

### 14.4 GitHub Actions VitePress Workflow（推荐模板）

文件名：`.github/workflows/vitepress-pages.yml`

```yaml
name: Deploy VitePress Docs to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: https://yeluo45.github.io/hermes-agent-design/
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: docs-site/pnpm-lock.yaml

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        working-directory: ./docs-site
        run: pnpm install --frozen-lockfile

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

**关键点**：
- `cache-dependency-path` 设为 `docs-site/pnpm-lock.yaml`（相对于仓库根）
- `pnpm install --frozen-lockfile` 需要 lockfile 存在
- artifact path 是 `.vitepress/dist`（VitePress 输出目录，不是 `dist`）

### 14.5 暗色主题 CSS 变量参考

```css
:root {
  --vp-c-bg: #0f0f23;
  --vp-c-bg-alt: #1a1a2e;
  --vp-c-bg-elv: #16162a;
  --vp-c-text-1: #e0e0e0;
  --vp-c-text-2: #aaa;
  --vp-c-brand-1: #00d4ff;
  --vp-c-brand-2: #00b8e6;
  --vp-c-divider: #2a2a4a;
  --vp-nav-bg-color: #1a1a2e;
  --vp-sidebar-bg-color: #1a1a2e;
  --vp-code-block-bg: #0d0d1a;
}
```

### 14.6 config.mjs 关键配置

```js
import { defineConfig } from "vitepress";

export default defineConfig({
  title: "Hermes Agent Design",
  description: "Hermes Agent 架构设计文档站",
  lang: "zh-CN",

  themeConfig: {
    logo: '/logo.svg',
    nav: [
      { text: '首页', link: '/' },
      { text: 'API', link: '/api' },
      // ...
    ],
    sidebar: [{
      text: '文档',
      items: [
        { text: '首页', link: '/' },
        { text: 'API', link: '/api' },
        // ...
      ],
    }],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/YeLuo45/hermes-agent-design' },
    ],
  },
});
```

### 14.7 npm install 超时解决

**症状**：`npm install` 或 `pnpm install` 在 WSL 环境下超时（300s 内无法完成）。

**方案 A**：使用 GitHub Actions 云端构建（推荐，本地不需安装依赖）
```bash
# 只在本地验证 Markdown 内容，不做完整构建
# push 到 main 分支，由 GitHub Actions 执行 pnpm install + build
```

**方案 B**：预装依赖
```bash
# 如果 node_modules 已存在（之前安装过），直接 build
cd docs-site && pnpm run build
```

**方案 C**：pnpm install CI 模式
```bash
CI=true pnpm install
```

### 14.8 SSL EOF 导致 API 推送失败

**症状**：GitHub REST API 在获取 SHA 时报 SSL EOF 错误（网络不稳定）。
```python
requests.exceptions.SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol
```

**解决**：添加重试逻辑，每次请求间隔 2-3 秒。
```python
def get_sha(path):
    for attempt in range(3):
        try:
            r = requests.get(f'{BASE}/repos/{REPO}/contents/{path}', headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()['sha']
            return None
        except:
            time.sleep(2)
    return None
```

### 14.9 切换 GitHub Pages 到 VitePress

hermes-agent-design 的旧系统（根目录 .html）仍在服务。如需切换到 VitePress：

1. 修改 `.github/workflows/pages.yml` 的 artifact path：
   ```yaml
   # 旧：path: '.'
   # 新：
   path: ./docs-site/.vitepress/dist
   ```

2. 删除根目录的旧 HTML 文件（或移出 GitHub Pages 源）

### 14.10 并行创建 Markdown 文件流程

hermes-agent-design 案例：创建 7 个 Markdown 文件分两批：

**第一批**（3 个）：index.md, api.md, dashboard.md
```python
delegate_task(tasks=[
    {"goal": "index.md content", "context": "...", "toolsets": ["file"]},
    {"goal": "api.md content", "context": "...", "toolsets": ["file"]},
    {"goal": "dashboard.md content", "context": "...", "toolsets": ["file"]},
])
```

**第二批**（3 个）：mcp.md, agent-runner.md, platform-adapter.md
```python
delegate_task(tasks=[
    {"goal": "mcp.md content", ...},
    {"goal": "agent-runner.md content", ...},
    {"goal": "platform-adapter.md content", ...},
])
```

**第 7 个**（plugin-development.md）已存在，无需创建。

**教训**：一次委托 ≤ 3 个任务，`max_concurrent_children` 限制为 3。

### 14.11 交付验收清单

hermes-agent-design VitePress 交付验收：
- [ ] 首页 `https://yeluo45.github.io/hermes-agent-design/` HTTP 200
- [ ] 导航栏 7 个链接全部指向正确页面
- [ ] API 子页面内容完整（表格、代码块正常渲染）
- [ ] 暗色主题 CSS 生效（背景 #0f0f23、强调色 #00d4ff）
- [ ] GitHub Actions 构建日志无错误

---

## 15. 参考资料

- VitePress 官方文档：https://vitepress.dev/
- VitePress GitHub：https://github.com/vuejs/vitepress
- trading-agent-design: https://yeluo45.github.io/trading-agent-design/
- astrbot-design: https://yeluo45.github.io/astrbot-design/
- hermes-agent-design: https://yeluo45.github.io/hermes-agent-design/
- GitHub Pages: https://pages.github.com/
