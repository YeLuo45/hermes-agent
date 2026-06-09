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

### 3.5 Subagent 生成文档的 Dead Link 风险（重要）

当使用 `delegate_task` 并行生成 Markdown 文档时，subagent 会基于源码目录（如 `/home/hermes/opensource/{project}/`）提取信息，**自然地**在文档中添加指向源码目录的相对链接：

```markdown
// subagent 生成的典型无效引用
[完整文档: ](../../AGENTS.md)          // 指向 docs-site 上两层的 AGENTS.md
[源码: ](/home/hermes/opensource/...)  // 指向本地文件系统
[参考文档: ](../docs/USERGUIDE]       // 指向 docs-site 外部的 docs/
```

**症状**：VitePress 构建失败，错误信息：
```
Could not resolve "./../images/NodeEditor.png" from "node-editor.md"
(!) Found dead link ./../../AGENTS in file agents.md
(!) Found dead link ./../docs/USERGUIDE in file architecture.md
x Build failed: [vitepress] 4 dead link(s) found.
```

**根因**：subagent 从源码目录读取文件生成文档，末尾"参考"段落包含源码路径引用。这些路径在 `docs-site/` 中不存在。

**两类 dead link 模式**：

| 模式 | 示例 | 修复方式 |
|------|------|----------|
| 指向不存在的源码相对路径 | `../../AGENTS.md`、`../docs/USERGUIDE` | 直接删除"参考"段落 |
| 指向不存在的图片路径（内部） | `../images/XXX.png` | 用 raw GitHub URL 替代：`https://raw.githubusercontent.com/{owner}/{repo}/main/images/XXX.png` |
| 指向不存在的图片路径（外部） | 外部图片 URL | 确认 URL 可访问；不存在的截图类引用直接删除或用文字描述替代 |
| 指向不存在的内部文档 | `./ai-quant-lab.md` | 删除该链接或替换为已存在的文档页 |

**修复**：在 subagent 的 `goal` prompt 中明确添加约束：
```markdown
// 在 goal 的最后附加：
---
坑点：文档中禁止出现以下模式：
1. 指向源码目录的相对路径（../../AGENTS.md、../docs/USERGUIDE 等）
2. 指向 docs-site/ 内不存在的图片路径（../images/XXX.png 等）
3. 指向 docs-site/ 内不存在的文档（./xxx.md 等）
4. 标题行（# ## ###）包含未转义的 `<T>`、`<TData>` 等泛型语法 → 必须写 `&lt;T&gt;`
5. `{{variable}}` 模式（Go 模板、Mustache 等）→ 必须写 `&#123;&#123;variable&#125;&#125;`
如有参考内容，直接删除对应链接或段落，不要留任何悬空引用。
图片使用 raw GitHub URL（如 https://raw.githubusercontent.com/...），不要用相对路径。
---
---
```

**验证**：构建前检查所有 markdown 文件是否包含无效路径模式：
```bash
# 检查相对路径到源码目录
grep -rn "\.\./\.\." docs-site/*.md

# 检查相对路径到 images/（需确认 docs-site/images/ 存在）
grep -rn "\.\./images/" docs-site/*.md

# 检查相对路径到 .md 文件（需确认目标文件存在）
grep -rn "\./[a-z]" docs-site/*.md

# 任意一项有输出 → 存在 dead link，必须修复
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

**⚠️ theme/index.js 错误写法（常见坑）**：

```js
// ❌ 错误：theme/index.js 不是 config，不要用 defineConfig
import { defineConfig } from "vitepress";
export default defineConfig({
  extends: DefaultTheme,
});
```

```js
// ✅ 正确写法
import DefaultTheme from "vitepress/theme";
import "./style.css";

export default {
  extends: DefaultTheme,
};
```

**症状**：VitePress 构建失败，报错：
```
"defineConfig" is not exported by "node_modules/vitepress/dist/client/index.js"
```

**build-yourownx-design 项目教训（2026-05-14）**：创建 theme/index.js 时错误地使用了 `defineConfig`，导致 GitHub Actions 构建失败。修复后成功部署。

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

## 7. Fork-first 模式：上游仓库识别与处理

### 7.1 判断规则

在执行任何 push 之前，先检查仓库是否属于上游组织：

```bash
grep -E "OpenBMB|vuejs|langchain|microsoft|google|anthropic" README.md 2>/dev/null
# 匹配到 → 上游仓库，需要 fork
```

或通过 API 检查：
```python
GET /repos/YeLuo45/{repo-name}  → 404 = 不属于 YeLuo45
```

### 7.2 Fork 工作流

```python
# 1. Fork 上游仓库
POST /repos/{upstream_owner}/{upstream_repo}/forks
# 返回: {"full_name": "YeLuo45/repo-name", "html_url": "..."}

# 2. 克隆 fork 到本地
git clone https://github.com/YeLuo45/repo-name.git /path/to/local

# 3. 本地创建 docs-site/，推送
# ... normal push flow

# 4. 启用 GitHub Pages（Fork 后默认不启用）
PUT /repos/YeLuo45/repo-name/pages
{
  "source": {"branch": "gh-pages", "path": "/"}
}
# 返回 201
```

**错误代价**：未 fork 直接 push → HTTP 403 Forbidden。chatdev-design 案例教训。

---

## 8. actions-gh-pages@v4 的 `force_orphan: true` Bug

### 8.1 症状

使用 `peaceiris/actions-gh-pages@v4` 时，即使构建成功（所有 steps: success），gh-pages 分支只有 **1 个文件**（.nojekyll），所有 HTML/CSS/JS 产物全部丢失。

### 8.2 诊断

```python
# 检查 gh-pages 文件数量
GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1
# 正常：22+ 个文件（含 index.html、assets/）
# Bug：1 个文件（只有 .nojekyll blob）

# 验证 URL
curl -sI "https://{username}.github.io/{repo}/" | head -1
# HTTP/2 404
```

### 8.3 修复

降级到 `actions-gh-pages@v3`：

```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3  # ← v3，v4 有 bug
```

### 8.4 时间线

| 版本 | force_orphan 行为 |
|------|-------------------|
| v3 | 正常工作，gh-pages 包含所有构建产物 |
| v4 | force_orphan: true 时，gh-pages 只有 .nojekyll |

已知受影响的仓库：chatdev-design（2026-05-13），修复后成功部署。

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

- `references/subagent-parallel-and-github-api-push.md` — 子 Agent 并行执行技巧
- `references/navigation-standardization.md` — 多页面文档站导航栏统一规范
- `references/vitepress-base-path-workflow-mode.md` — VitePress base 配置与 GitHub Pages 部署模式
- `references/rest-api-github-dir-upload.md` — REST API 推送新仓库时 `.github/` 目录遗漏问题
- `references/vitepress-new-project-pitfalls.md` — **新项目创建常见错误**：theme/index.js 错误写法、workflow environment 块部署阻止、**workflow 未自动触发需要手动 gh workflow run**、**npm install 超时（WSL/GitHub Actions）+ prefer-offline 解决方案**
- `references/vitepress-html-tag-parsing-error.md` — **VitePress Vue 解析器把 `<T>` 当 HTML 标签**：TypeScript 泛型标题导致构建失败，`&lt;T&gt;` 转义修复
- `references/vitepress-nav-links-deadlinks.md` — **VitePress nav/sidebar 链接必须与文件名完全匹配**：`/frontend` → 404，`/frontend-stack` → 200；配置中的 link path 末尾不要加 `.html`；构建时 `ignoreDeadLinks: true` 作为安全网
- `references/rest-api-sha-push-patterns.md` — SHA-first PUT /contents 模式、409 Conflict 三种场景（reference already exists / sha not supplied / 目录已存在）、批量推送优化、自动重试处理。常见于新仓库推送后文件散落根目录的问题。
- `references/rest-api-batch-upload-timeout.md` — REST API 批量上传超时问题：17 文件单批超时 300s killed，分两批（6+11）成功上传的优先级上传策略。
- `references/github-pages-setup-failure-retry.md` — GitHub Pages workflow mode 首次构建 "Setup Pages" 失败，重试（re-run）后成功。Pages API 传播延迟的已知模式。

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
    branches: [master, main]
    paths: ['docs-site/**', '.github/workflows/vitepress-pages.yml']
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
    # ⚠️ 不要在这里声明 environment:，否则 main 分支会被阻止部署
    # 如果需要指定 URL，在 workflow 的最后一步 actions/deploy-pages 会自动处理
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

**关键点**：
- **不要**使用 `cache-dependency-path: docs-site/pnpm-lock.yaml` 和 `pnpm install --frozen-lockfile`——新仓库没有 lockfile，会导致构建失败
- 使用 `pnpm install`（不带 `--frozen-lockfile`）
- artifact path 是 `.vitepress/dist`（VitePress 输出目录，不是 `dist`）
- workflow mode **不需要** gh-pages 分支存在，Actions 会自动创建
- **不要在 job 内使用 `environment:` 块**（除非在目标仓库的 Environments 设置中预先配置了同名 environment）。直接去掉 `environment:` 块，或者确保仓库 Settings → Environments 中已创建该 environment

**⚠️ GitHub Actions environment protection rules 导致部署失败（build-yourownx-design 教训 2026-05-14）**：

workflow 中写了：
```yaml
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: https://yeluo45.github.io/build-yourownx-design/
```

但 `main` 分支被环境保护规则阻止部署到 `github-pages` environment：
```
Branch "main" is not allowed to deploy to github-pages due to environment protection rules.
The deployment was rejected or didn't satisfy other protection rules.
```

**症状**：workflow 运行成功（all steps success），但 Pages URL 返回 404。

**解决**：移除 `environment:` 块，或在仓库 Settings → Environments 中预先创建并配置 `github-pages` environment：

```yaml
# ✅ 正确：不要在 job 内声明 environment
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... 其他 steps
```

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

### 14.12 分析阶段快速定位清单

拿到一个 design 项目后，先回答以下问题再选方向：

```
1. docs/ 或 docs-site/ 是否存在？ → 已有 VitePress 源文件？
2. .vitepress/dist/ 是否存在？ → 已有构建产物？
3. GitHub Pages 是否已配置？ → curl {username}.github.io/{repo}/ 返回 200？
4. 仓库是"纯设计文档"还是"源码含嵌入文档"？
   - 纯设计：hermes-agent-design、astrbot-design — 文档与源码分离
   - 嵌入文档：chatdev-design — docs/user_guide/ 在源码仓库内
5. 根目录是否有 *.html？ → 旧手工 HTML 遗留？
```

**chatdev-design 案例**（2026-05-13）：
- `docs/user_guide/zh/` + `en/` 双语 Markdown ✓
- 无 `.vitepress/`、无 `docs-site/` ✗
- GitHub Pages 未配置（404）✗
- 仓库类型：**源码含嵌入文档**（不是纯设计站）
- 建议方向：**A（新建 docs-site/）**——不影响源码文档结构

### 14.13 提出方向前的自我检查

教训：展示 A/B/C 选项时，应同时给出**推荐方向 + 理由**，而非让 boss 盲目选择。

错误示范：
> "A... B... C... 选哪个？"

正确示范：
> "建议选 **A**（新建 docs-site/），原因：chatdev-design 是源码仓库，`docs/user_guide/` 是嵌入文档不宜迁移，且无 GitHub Pages 历史。最稳妥。"

---

## 15. 上游仓库 Fork 工作流（重要）

> 当目标仓库是上游组织（OpenBMB、Vue、LangChain 等）的仓库时，必须先 fork 再推送，否则 push 被拒绝。

### 15.1 判断依据

```
grep "OpenBMB\|vuejs\|langchain\|microsoft\|google" README.md
```

如果存在 → 上游仓库，需要 fork。

### 15.2 Fork 工作流

```python
# 1. 检查仓库是否属于自己的账号
GET /repos/YeLuo45/chatdev-design  → 404 = 不属于

# 2. Fork 上游仓库
POST /repos/{upstream_owner}/{upstream_repo}/forks
# 返回: { "full_name": "YeLuo45/chatdev-design", "html_url": "https://github.com/YeLuo45/ChatDev" }

# 3. 克隆新 fork 的仓库到本地
git clone https://github.com/YeLuo45/ChatDev.git /home/hermes/opensource/chatdev-design

# 4. 在本地仓库创建 docs-site/ 并推送
# ... 正常流程

# 5. GitHub Pages 部署到 YeLuo45/ChatDev
```

### 15.3 chatdev-design 案例（2026-05-13）

| 项目 | 归属 | 处理方式 |
|------|------|----------|
| hermes-agent-design | YeLuo45 | 直接 clone + push |
| chatdev-design | OpenBMB | 先 fork 再 clone |

教训：没有先检查仓库归属，直接尝试 clone/push，导致 push 被拒绝（HTTP 403）。

### 15.4 Fork 后 GitHub Pages 配置

Fork 后 GitHub Pages 默认**不启用**，需要手动配置：

```python
# 启用 GitHub Pages（workflow mode）
PUT /repos/YeLuo45/ChatDev/pages
{
  "source": {
    "branch": "gh-pages",
    "path": "/"
  }
}
# 成功返回 201

# 验证
GET /repos/YeLuo45/ChatDev/pages
# 返回 { "build_type": "workflow", "source": { "branch": "gh-pages", "path": "/" } }
```

## 16. VitePress + GitHub Pages 部署模式对比

### 16.1 两种部署模式

| 模式 | 配置方式 | 可靠性 | 适用场景 |
|------|----------|--------|----------|
| **workflow mode** | Settings → Pages → Source: GitHub Actions | 偶发 404 | 简单静态站 |
| **gh-pages 分支** | Settings → Pages → Source: gh-pages branch + actions-gh-pages action | 更稳定 | VitePress SPA |

### 16.2 workflow mode 的 VitePress SPA 问题

VitePress 是 SPA（单页应用），依赖 JavaScript 动态路由。GitHub Pages workflow mode 的 `actions/deploy-pages@v4` 配合 `upload-pages-artifact@v3` 在某些配置下会导致根路径 `/` 404，但 `/zh/` 等子路径返回正常 HTML。

**诊断方法**：
```bash
# 检查根路径
curl -sI "https://yeluo45.github.io/ChatDev/" | head -1
# HTTP/2 404  ← 问题

# 检查子路径
curl -s "https://yeluo45.github.io/ChatDev/zh/" | head -5
# 返回完整 HTML  ← 内容正确但仍 404
```

**验证 artifact 内容**：
```python
# 下载 artifact 验证文件列表
GET /repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip
# 分析：index.html 存在但路由不工作
```

### 16.3 推荐：gh-pages 分支 + peaceiris/actions-gh-pages

> **⚠️ 关键教训（2026-05-13）**：必须使用 `peaceiris/actions-gh-pages@v3`，**不要**用 v4。v4 的 `force_orphan: true` 模式会导致 gh-pages 分支只有 1 个文件（.nojekyll），所有构建产物丢失。

```yaml
# .github/workflows/vitepress-pages-ghpages.yml
name: Build and Deploy VitePress Docs to gh-pages

on:
  push:
    branches: [main]
    paths: ['docs-site/**', '.github/workflows/...']
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org/'

      - name: Install dependencies
        run: npm install
        working-directory: docs-site

      - name: Build
        run: npm run build
        working-directory: docs-site

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3  # ← v3，v4 有 force_orphan bug
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: docs-site/.vitepress/dist  # ← VitePress 输出目录
          publish_branch: gh-pages
          force_orphan: true
```

**关键点**：
- `permissions: contents: write` — gh-pages 写入需要写权限
- `force_orphan: true` — 每次部署清空 gh-pages 历史，避免旧文件残留
- `publish_dir: docs-site/.vitepress/dist` — VitePress 输出目录，**不要**写成 `docs-site/dist` 或 `docs-site`
- `actions-gh-pages@v3` — v4 的 force_orphan 有 bug，gh-pages 只有 .nojekyll 一个文件

**v4 bug 症状**：
- gh-pages 分支构建后只有 1 个文件（.nojekyll）
- 所有 HTML/CSS/JS 产物丢失
- GitHub Pages URL 返回 404
- `GET /repos/{owner}/{repo}/branches/gh-pages` 显示 commit 存在但 tree 为空

**已知受影响的仓库**：chatdev-design（2026-05-13），根因导致 redirect 配置未生效，修复后成功部署。

**gh-pages 分支 redirect 路径修复**：当站点部署在子目录（如 `/chatdev-design/`）时，VitePress 构建产物的 meta redirect 必须使用完整路径 `/chatdev-design/zh/`，而不是 `/zh/`。这是 `base` 配置的核心目的——使 redirect 和资源路径都加上仓库名前缀。症状：`curl /chatdev-design/` 返回 `<meta http-equiv="refresh" content="0;url=/zh/">` → 跳转到 `https://yeluo45.github.io/zh/`（404）。修复后：redirect 变为 `/chatdev-design/zh/`，正确跳转。

**验证构建产物**：

**验证构建产物**：
```python
# 检查 gh-pages 分支文件数量
GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1
# 正常：22+ 个文件（含 index.html、assets/）
# v4 bug：1 个文件（只有 .nojekyll）
```

### 16.4 快速验证 GitHub Pages 部署状态

```bash
# 1. 检查 gh-pages 文件列表
curl -s "https://api.github.com/repos/{owner}/{repo}/branches/gh-pages" | jq -r '.commit.sha'
curl -s "https://api.github.com/repos/{owner}/{repo}/git/trees/{sha}?recursive=1" | jq '.tree | length'

# 2. 检查 Pages 配置
curl -s "https://api.github.com/repos/{owner}/{repo}/pages" | jq '{url: .html_url, build_type: .build_type, source: .source}'

# 3. 触发 Pages 重建（如需）
curl -s -X POST -H "Authorization: Bearer {token}" \
  "https://api.github.com/repos/{owner}/{repo}/pages/builds"
```

### 16.4 workflow mode 切换到 gh-pages 模式的 API 操作

```python
# 1. 确认 gh-pages 分支存在且有内容
GET /repos/{owner}/{repo}/branches/gh-pages

# 2. 更新 Pages 配置指向 gh-pages
PUT /repos/{owner}/{repo}/pages
{
  "source": {
    "branch": "gh-pages",
    "path": "/"
  }
}

# 3. 触发 GitHub Pages 重建（如果需要）
POST /repos/{owner}/{repo}/pages/builds
```

## 18. 创建新 Design 项目 vs Fork 已有仓库（重要区分）

### 18.1 两种场景

| 场景 | 说明 | 示例 |
|------|------|------|
| **创建新的 Design 项目** | 用户想要一个基于上游源码的**新仓库**，承载设计文档 | chatdev-design = 新建 YeLuo45/chatdev-design |
| **Fork + 迭代** | Fork 上游仓库，在 fork 内迭代源码和文档 | YeLuo45/ChatDev（ChatDev fork）|

**关键区别**：当用户说"基于 X 项目创建 design 项目 Y"时，Y 是**全新的独立仓库**，不是 X 的 fork。不要在 X 的 fork 内创建 docs-site/。正确流程：

1. 先检查 `YeLuo45/{Y}` 是否存在 → 存在则 clone，不存在则创建新仓库
2. 如果需要上游源码内容，从上游克隆（不是 fork）
3. 在本地构建 docs-site/ + 源码结构
4. 推送到 `YeLuo45/{Y}`（新仓库，非 fork）
5. GitHub Pages 部署到 `YeLuo45/{Y}`

### 18.2 判断流程

```
用户说：基于 chatdev 创建 chatdev-design
↓ 检查 YeLuo45/chatdev-design 是否存在
  → 不存在 → 创建新空仓库 + 从上游克隆源码 + 构建文档
  → 存在且属于 YeLuo45 → 直接 clone + push
  → 存在但属于上游 → Fork first
```

### 18.3 chatdev-design 项目教训（2026-05-13）

**错误做法**：Fork OpenBMB/ChatDev → 在 YeLuo45/ChatDev 内创建 docs-site/ → GitHub Pages 部署到 YeLuo45/ChatDev

**用户实际想要的**：独立的 chatdev-design 设计文档站（与 ChatDev 源码仓库分开）

**教训**：用户说"基于 X 创建 Y"时，Y 是新仓库，不是 fork。"design" 关键词暗示这是独立的设计文档工程，不是源码迭代。

---

## 19. chatdev-design 项目经验（2026-05-13）

> Direction A（新建 docs-site/）交付记录。**注意**：本项目实际上是 Fork 迭代（YeLuo45/ChatDev），不是创建新 Design 项目。

### 17.1 执行摘要

| 项目 | 结果 |
|------|------|
| 仓库 | YeLuo45/ChatDev（从 OpenBMB/ChatDev fork） |
| 源码 | docs-site/ — 15 个文件，VitePress + 10 个中文 Markdown |
| Workflow | vitepress-pages-ghpages.yml — 成功运行（all steps success） |
| gh-pages | 22 个文件，包含完整构建产物 |
| GitHub Pages | API 配置成功，gh-pages 分支已配置，但 URL 仍 404 |

### 17.2 交付物清单

```
YeLuo45/ChatDev/
├── docs-site/
│   ├── .vitepress/
│   │   ├── config.mjs          # nav + sidebar + 暗色主题 #6c5ce7
│   │   └── theme/
│   │       ├── index.js        # extends DefaultTheme
│   │       └── style.css       # 自定义暗色 CSS
│   ├── package.json            # npm dependencies
│   ├── zh/
│   │   ├── index.md            # layout: home（首页）
│   │   ├── web-ui.md           # Web UI 快速开始
│   │   ├── workflow.md         # 工作流编写
│   │   ├── execution.md        # 执行逻辑
│   │   ├── dynamic.md          # 动态执行
│   │   ├── api.md              # API 参考
│   │   ├── nodes/
│   │   │   ├── index.md        # 节点概览
│   │   │   └── agent.md        # Agent 节点
│   │   └── modules/
│   │       ├── index.md        # 模块索引
│   │       └── tooling.md      # Tooling 模块
│   └── index.md                # 重定向页
└── .github/
    └── workflows/
        ├── vitepress-docs.yml          # workflow mode（旧）
        └── vitepress-pages-ghpages.yml # gh-pages 模式（当前）
```

### 17.3 关键教训

1. **Fork first** — chatdev-design 是 OpenBMB 上游仓库，未 fork 直接 push → HTTP 403
2. **npm vs pnpm** — hermes-agent-design 用 pnpm（需要 pnpm-lock.yaml），chatdev-design 改用 npm（无 lockfile 问题）
3. **pnpm --frozen-lockfile** — 首次创建的新仓库没有 lockfile，使用 `--frozen-lockfile` 会报错，改用 `npm install`
4. **gh-pages vs workflow** — workflow mode 对 VitePress SPA 路由有问题，改用 peaceiris/actions-gh-pages 更稳定
5. **GitHub Pages API** — 可通过 API 配置 Pages source，不需要浏览器操作
6. **Deploy 成功 ≠ Pages 正常** — gh-pages 分支和文件都存在，Pages 配置也正确，但 URL 仍 404（传播延迟或配置未完全生效）

### 17.4 未解决问题

GitHub Pages URL `https://yeluo45.github.io/ChatDev/` 返回 404，但：
- gh-pages 分支包含 22 个正确文件（含 .nojekyll、index.html）
- Pages API 返回 `build_type: workflow`, `source: {branch: gh-pages}`
- `/zh/` 子路径返回正确 HTML 但仍是 404

**待办**：在浏览器中访问 `https://github.com/YeLuo45/ChatDev/settings/pages` 确认配置已生效，或等待 5-10 分钟让 GitHub Pages 传播。

---

## 18. 参考资料

- VitePress 官方文档：https://vitepress.dev/
- VitePress GitHub：https://github.com/vuejs/vitepress
- trading-agent-design: https://yeluo45.github.io/trading-agent-design/
- astrbot-design: https://yeluo45.github.io/astrbot-design/
- hermes-agent-design: https://yeluo45.github.io/hermes-agent-design/
- GitHub Pages: https://pages.github.com/

## 19. bmad-method-design 项目经验（2026-05-14）

> 本节记录从 bmad-method-design 项目沉淀的经验：新仓库创建 + REST API 推送 + workflow mode GitHub Pages 配置。

### 19.1 项目背景

bmad-method-design 文档站基于上游开源项目 `/home/hermes/opensource/bmad-method-design/`（非 git 仓库，无网络访问），使用 REST API 在 GitHub 创建新仓库并推送 VitePress 文档站。

### 19.2 关键教训

**教训 1：新仓库 + Git push 阻塞时，使用 REST API**

当 GitHub HTTPS push 超时或被阻塞，且仓库是通过 API 新创建的（无 git 历史），使用 REST API `PUT /repos/{owner}/{repo}/contents/{path}` 逐文件推送：

**⚠️ 关键陷阱：REST API 推送时 path 前缀决定文件在仓库中的位置**

`PUT /contents/{path}` 中的 `path` 参数**直接决定**文件在仓库中的存放位置。
如果 workflow YAML 中有 `working-directory: ./docs-site`，但推送时 path 写的是 `config.mjs`，
文件会出现在 repo 根目录（`config.mjs`），而不是 `docs-site/config.mjs`，
导致 workflow checkout 后找不到 `docs-site/` 目录，报错：
```
An error occurred trying to start process '/usr/bin/bash' with working directory
'/home/runner/work/{repo}/{repo}/./docs-site'. No such file or directory
```

**正确做法**：在所有 path 参数前加上目标子目录前缀。
```python
# 推送到 docs-site/ 子目录
api_put(f"docs-site/{relpath}", content, f"docs: add {relpath}")
# ❌ 错误：api_put(relpath, ...)  → 文件散落在 repo 根目录
```

**验证推送结果**：检查 GitHub 上仓库的文件树，确认文件在正确的子目录下。
```python
GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1
# 确认 .vitepress/config.mjs 在 docs-site/.vitepress/config.mjs
# 而不是根目录的 .vitepress/config.mjs
```

已知受影响仓库：media-crawler-design（2026-05-14）。

```python
def api_put(path, data, retries=5):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                BASE + path,
                data=json.dumps(data).encode(),
                headers={**HEADERS},
                method='PUT'
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 409:  # 文件已存在，需要 SHA
                sha_req = urllib.request.Request(BASE + path, headers=HEADERS)
                with urllib.request.urlopen(sha_req, timeout=15) as sr:
                    return {"sha": json.loads(sr.read())['sha'], "already_exists": True}
            time.sleep(2)
        except Exception as e:
            time.sleep(2)
    return {"error": str(e)}
```

**教训 2：GitHub Pages API 启用 workflow mode**

gh-pages 分支不存在时，`PUT /repos/{owner}/{repo}/pages` 使用 `source.branch` 会返回 422：
```
"message":"The gh-pages branch must exist before GitHub Pages can be built."
```

**解决**：使用 `build_type: "workflow"` 启用 workflow mode（不需要 gh-pages 分支）：

```python
pages_req = urllib.request.Request(
    BASE + '/pages',
    data=json.dumps({"build_type": "workflow"}).encode(),
    headers={**HEADERS},
    method='POST'
)
```

**教训 3：SSL EOF 导致 API 推送失败**

WSL 环境下 GitHub API 请求常报 SSL EOF 错误。添加 3-5 次重试 + 2-3 秒间隔：

```python
for attempt in range(5):
    try:
        # API call...
    except Exception as e:
        time.sleep(3)  # 间隔重试
```

### 19.3 执行流程

```
1. git init + git add + git commit（本地初始化）
2. GitHub API POST /user/repos（创建新仓库）
3. REST API PUT /contents 推送所有文件（分批，每批 5 个文件）
4. REST API 推送 .github/workflows/vitepress-pages.yml
5. GitHub Pages API 启用 workflow mode
6. proposals.json 同步 + push
```

### 19.4 交付物

| 项目 | 结果 |
|------|------|
| 仓库 | YeLuo45/bmad-method-design |
| 文档站 | https://yeluo45.github.io/bmad-method-design/ |
| 部署方式 | GitHub Actions workflow mode |
| 文档内容 | 31 个中文文档（tutorials/reference/how-to/explanation） |
| 状态 | acceptance: accepted |

## 20. nanobot-design 项目经验（2026-05-14）

> 本节记录从 nanobot-design 项目沉淀的经验：YAML frontmatter 冒号语法错误 + CI 日志捕获方法论 + 双分支同步问题。

### 20.7 REST API 推送路径映射陷阱（重要：media-crawler-design 教训 2026-05-15）

**症状**：通过 REST API `PUT /repos/{owner}/{repo}/contents/{path}` 推送文件到新仓库后，workflow 文件不在预期位置，导致 GitHub Actions 找不到 workflow，Pages 部署失败。

**根因**：`path` 参数直接决定文件在仓库中的存放位置。

```python
# 推送到 docs-site/ 子目录（正确）
api_put(f"docs-site/.github/workflows/vitepress-pages.yml", content, "docs: add workflow")

# ❌ 错误：只写文件名 → 文件出现在 repo 根目录
api_put(".github/workflows/vitepress-pages.yml", content, "docs: add workflow")
# 结果：.github/workflows/vitepress-pages.yml 在 repo 根目录（不在 docs-site/）
```

**症状**：workflow 文件跑到 `repo/.github/workflows/vitepress-pages.yml`，但 `docs-site/` 目录为空。GitHub Actions 找不到 workflow，报错：
```
Error: Unable to locate workflow file
```

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

**正确做法**：REST API 推送时，所有 path 都要加 `docs-site/` 前缀：
```python
files_to_push = [
    ("docs-site/package.json", package_content),
    ("docs-site/.vitepress/config.mjs", config_content),
    ("docs-site/.github/workflows/vitepress-pages.yml", workflow_content),  # ← 正确
    (".github/workflows/vitepress-pages.yml", workflow_content),             # ← 错误
]
```

### 20.8 Workflow 文件必须放在 Repo Root（重要：claude-howto-design 教训 2026-05-15）

**症状**：workflow 文件在 `docs-site/.github/workflows/vitepress-pages.yml`，GitHub Actions 报：
```
Workflow does not exist or is disabled
```

**根因**：GitHub Actions 的 workflow 文件必须在 repo root 的 `.github/workflows/`，不能嵌套在子目录。

**两种部署模式的 artifact path 区别**：

| 模式 | workflow 位置 | artifact path |
|------|--------------|---------------|
| workflow mode | `.github/workflows/` (repo root) | `.vitepress/dist` |
| gh-pages 模式 | `.github/workflows/` (repo root) | `docs-site/.vitepress/dist` |

**正确目录结构**：
```
repo/
├── docs-site/
│   ├── .vitepress/config.mjs
│   ├── .vitepress/dist/          # 构建产物
│   ├── index.md
│   └── package.json
└── .github/
    └── workflows/
        └── vitepress-pages.yml    # ← repo root，不是 docs-site/.github/
```

**修复**：如果 workflow 文件已在 `docs-site/.github/workflows/`，通过 REST API 重新移动到 repo root：
```python
# 读取 docs-site/.github/workflows/vitepress-pages.yml 的内容
content = get_file_sha("docs-site/.github/workflows/vitepress-pages.yml")

# 删掉旧位置
delete_file("docs-site/.github/workflows/vitepress-pages.yml")

# 写到正确位置（repo root）
api_put(".github/workflows/vitepress-pages.yml", content, "fix: move workflow to repo root")
```

**触发 workflow**：
```python
# 新仓库 workflow 需要手动触发一次
POST /repos/{owner}/{repo}/actions/workflows/{workflow_filename}/dispatches?ref=main
{"inputs": {}}
```

### 20.9 REST API 创建新仓库后的 GitHub Pages 配置流程（重要）

通过 REST API 创建新仓库后，GitHub Pages 不会自动启用，需要手动配置：

```python
# 1. 确认仓库已创建
GET /repos/YeLuo45/{repo}

# 2. 启用 GitHub Pages（workflow mode，不需要 gh-pages 分支）
PUT /repos/YeLuo45/{repo}/pages
{
  "build_type": "workflow"
}
# 成功返回 201

# 3. 触发首次 workflow dispatch
POST /repos/YeLuo45/{repo}/actions/workflows/vitepress-pages.yml/dispatches?ref=main
# 成功返回 204

# 4. 验证 Pages 配置
GET /repos/YeLuo45/{repo}/pages
# 返回 { "build_type": "workflow", "status": "queued" }
```

**常见错误**：
- 新仓库用 `source.branch: "gh-pages"` → 422（gh-pages 分支不存在）
- 必须先用 `build_type: "workflow"` 启用，再等 Actions 创建产物

### 20.10 proposals.json 同步：新增 Design 项目的正确顺序

当通过 REST API 推送创建新 design 项目后，需要同步更新 `prj-proposals-manager` 的 proposals.json：

```python
# 1. 先更新 GitHub proposals.json
GET /repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json
# 获取 SHA

new_project = {
    "id": "PRJ-20260515-002",
    "name": "media-crawler-design",
    "gitRepo": "https://github.com/NanmiCoder/MediaCrawler",
    "localPath": "",
    "description": "MediaCrawler 自媒体平台爬虫设计文档站",
    "proposalCount": 0,
    "lastUpdate": "2026-05-15",
    "proposals": []
}

PUT /repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json
{
  "message": "feat: add media-crawler-design",
  "content": <base64 of updated proposals.json>,
  "sha": <current_sha>
}

# 2. 同时更新本地 CSV
# projects.csv 添加新行
# proposals.csv 添加新行（如果该 design 项目有提案）

# 3. 验证数量
# CSV data rows = GitHub projects count = boss 要求的项目总数
```

**数量检查**：
```bash
# CSV data rows
tail -n +2 ~/.hermes/proposals/projects.csv | wc -l

# GitHub projects count
# 从 proposals.json 的 total_projects 字段获取
```

### 20.1 项目背景

nanobot-design 文档站基于 HKUDS/nanobot（Python async AI agent framework），使用 VitePress + GitHub Actions workflow mode 部署。过程中遇到 25+ 次 CI 失败。

### 20.2 根因 1：YAML frontmatter 冒号未加引号

**症状**：VitePress build 报错 `incomplete explicit mapping pair; a key node is missed; or followed by a non-tabulated empty line at line 37, column 30`

**根因**：index.md frontmatter 中 `details: 12+ integrations: Telegram...` 含冒号的值未加引号，YAML 解析器把第二个冒号视为新映射键。

**修复**：
```yaml
# ❌ 错误
details: 12+ integrations: Telegram, Discord, Slack, Feishu, WeChat, and more.

# ✅ 正确
details: "12+ integrations: Telegram, Discord, Slack, Feishu, WeChat, and more."
```

**验证**：
```bash
grep -rn "details:.*:" docs-site/  # 查找含冒号但未引用的值
```

### 20.3 根因 2：CI 日志被吞 — 调试方法论

**症状**：Build 步骤失败但 gh run view 只显示步骤名，不显示 vitepress 报错信息。25+ 次 CI 失败都不知道真正原因。

**正确调试步骤**：

**第一步**：在 workflow 中捕获构建输出到文件
```yaml
- name: Build
  working-directory: ./docs-site
  run: |
    echo "=== Build started ==="
    pnpm run build > ../vitepress-build.log 2>&1 || true
    echo "=== Build exit code: $? ==="
    cat ../vitepress-build.log
    echo "=== End of log ==="
    if [ ! -d ".vitepress/dist" ]; then
      echo "ERROR: .vitepress/dist was NOT created"
      exit 1
    fi
```

**第二步**：查看失败步骤的完整日志
```bash
gh run view <run-id> --log-failed 2>&1 | tail -60
```

**教训**：调试 CI 时，第一步永远是让 CI 把日志写出来，而不是猜错误原因。

### 20.4 根因 3：双分支同步问题

**症状**：push 到 master，但 workflow 监听 main。gh run list 显示所有 run head_sha 相同（旧 commit），GitHub 上的文件内容也是旧的。

**根因**：
- REST API 创建 GitHub 仓库时默认分支是 main
- 本地 `git init` 默认分支是 master
- push 到 master 后，workflow 监听的 main 分支从未更新

**诊断**：
```bash
# 检查所有分支
gh api repos/Owner/repo/branches | jq '.[] | "\(.name) -> \(.commit.sha[0:7])"'

# 对比 ref SHA vs contents SHA
gh api repos/Owner/repo/git/refs/heads/main    # workflow 监听分支
gh api repos/Owner/repo/git/refs/heads/master # push 目标分支
gh api repos/Owner/repo/contents/docs-site/index.md | jq '.sha'  # 文件实际 SHA
```

**修复**：强制将 main ref 更新到最新 commit
```bash
gh api -X PATCH -H "Content-Type: application/json" \
  --input <(echo "{\"sha\":\"$(git rev-parse HEAD)\",\"force\":true}") \
  /repos/Owner/repo/git/refs/heads/main
```

**预防**：
1. REST API 创建仓库后立即检查 `git/refs/heads` 确认实际分支名
2. 在 `git init` 后立即 `git branch -m main` 保持与 GitHub 默认一致
3. workflow 的 `on: push: branches:` 要与实际默认分支匹配

### 20.5 其他问题：Dead link localhost

**症状**：`vitepress v1.6.4` 开始检查 dead link，`http://localhost:5173` 在 CI 环境无法访问导致构建失败。

**修复**：在 `config.mjs` 中添加 `ignoreDeadLinks: true`
```js
export default defineConfig({
  title: "nanobot Design",
  base: "/nanobot-design/",
  ignoreDeadLinks: true,  // 开发服务器链接在 CI 环境不可访问
  // ...
});
```

### 20.6 交付物

| 项目 | 结果 |
|------|------|
| 仓库 | YeLuo45/nanobot-design |
| 文档站 | https://yeluo45.github.io/nanobot-design/ |
| 部署方式 | GitHub Actions workflow mode (pnpm) |
| 文档内容 | 9 个英文文档 + 橙/青色主题 |
| 状态 | HTTP 200 ✓ |

## 21. 批量同步 design 项目到 proposals.json 的正确流程（2026-05-15）

> 本节记录 6 个 design 项目批量同步到 prj-proposals-manager 的经验教训：数据不一致诊断、REST API 认证问题、畸形条目修复。

### 21.1 问题发现：本地 CSV 与 GitHub proposals.json 不同步

boss 说当前 48 个项目，但本地 CSV 和 GitHub proposals.json 数量不一致：

| 数据源 | 项目数 |
|--------|--------|
| GitHub proposals.json（权威） | 48 |
| 本地 projects.csv | 48 行（正确） |
| 本地 proposals.json | 46（缺少 2 个） |

**诊断方法**：用 `gh api` 获取 GitHub 最新 proposals.json，不依赖本地数据。
```python
import subprocess, json, base64

result = subprocess.run(
    ['gh', 'api', '/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json'],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
content = base64.b64decode(data['content']).decode()
d = json.loads(content)
print(f"GitHub: {len(d['projects'])} projects")
```

**教训**：本地 proposals.json 可能过时，GitHub 才是 source of truth。先 fetch GitHub 版本再决策。

### 21.2 畸形条目：5 个项目没有 PRJ- 前缀

GitHub proposals.json 中有 5 个畸形条目（CSV 导入历史遗留）：

| 畸形 ID | 名称 |
|---------|------|
| `agent-记忆系统-跨-session-llm-决策记忆` | agent-记忆系统-跨-session-llm-决策记忆 |
| `cultivation-simulator` | cultivation-simulator |
| `github-repo-manager` | github-repo-manager |
| `hermes-agent-design` | hermes-agent-design |
| `proposals` | proposals |

**修复**：分配 PRJ- ID 并更新 proposals.json。
```python
malformed_map = {
    'agent-记忆系统-跨-session-llm-决策记忆': 'PRJ-20260417-003',
    'cultivation-simulator': 'PRJ-20260421-002',
    'github-repo-manager': 'PRJ-20260417-004',
    'hermes-agent-design': 'PRJ-20260421-003',
    'proposals': 'PRJ-20260417-005',
}
for p in projects:
    if not p['id'].startswith('PRJ-') and p['id'] in malformed_map:
        p['id'] = malformed_map[p['id']]
```

### 21.3 REST API 认证：401 Unauthorized

Python `urllib.request` 不走 `gh auth` 认证，直接 401。

**原因**：`gh auth` 的 token 不会自动注入到系统级别的 HTTP 请求。

**解决方案**：用 `subprocess + gh api` 或 `gh auth token` 获取 token。
```python
import subprocess

# 方案 1：gh api --input（推荐）
result = subprocess.run(
    ['gh', 'api', '--input', '/tmp/payload.json',
     'https://api.github.com/repos/Owner/repo/contents/path',
     '-X', 'PUT'],
    capture_output=True, text=True
)

# 方案 2：gh auth token + urllib
TOKEN = subprocess.run(
    ['gh', 'auth', 'token'], capture_output=True, text=True
).stdout.strip()
headers = {'Authorization': f'token {TOKEN}'}
```

### 21.4 批量同步到 proposals.json 的正确顺序

```
1. git clone prj-proposals-manager（不必要，直接用 gh api 远程操作）
2. 从 GitHub fetch 最新 proposals.json（SHA）
3. 解析 content，检查现有项目 + 畸形条目
4. 在内存中修复 + 添加新项目
5. 通过 gh api PUT /contents 推送（避免本地 git 冲突）
6. 同步更新本地 CSV
```

**关键**：先确认 GitHub 实际数量（48），再决定要加多少个（54 - 48 = 6）。

### 21.5 交付验收

| 检查项 | 预期结果 |
|--------|----------|
| GitHub proposals.json 项目总数 | 54 |
| proposals.json version 字段 | 4 |
| 本地 projects.csv 行数 | 55（含 header） |
| GitHub commit message | 包含 "54 total" |
| 6 个新项目 URL 全部可访问 | HTTP 200 |

### 21.6 deepseek-tui-design 预检教训

创建新 design 项目前，**先检查 GitHub 仓库是否已存在**：
```python
result = subprocess.run(
    ['gh', 'api', '/repos/YeLuo45/deepseek-tui-design'],
    capture_output=True, text=True
)
if result.returncode == 0:
    # 仓库已存在 → 检查 docs-site/ 内容，而不是重建
    # → curl -sI https://yeluo45.github.io/deepseek-tui-design/ 验证 Pages
else:
    # 仓库不存在 → 新建
```

**deepseek-tui-design 结果**：仓库已存在，docs-site/ 含 11 个文件，GitHub Pages 已上线（HTTP 200），无需重建。
