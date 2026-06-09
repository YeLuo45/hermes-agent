---
name: design-web
description: VitePress 设计文档站点的创建、构建与 GitHub Pages 部署 — 适用架构文档、API 文档、设计规范等静态文档站点
category: software-development
---

# design-web

VitePress 设计文档站点从初始化到 GitHub Pages 部署的完整流程。

## 适用场景

- 架构设计文档（AstrBot Design 类型）
- API 接口文档
- 产品设计规范
- 开源项目文档

## 目录结构

```
docs-site/                  # 文档站点根目录
├── .vitepress/
│   ├── config.mjs          # VitePress 配置（必须 .mjs 扩展名，ESM 语法）
│   ├── theme/              # 自定义主题
│   ├── public/             # 静态资源（favicon、logo 等）
│   └── dist/               # 构建产物（自动生成）
├── public/                 # 文档静态资源
├── *.md                    # 文档页面
├── package.json
└── pnpm-lock.yaml
```

## 初始化

```bash
mkdir docs-site && cd docs-site
npm init -y
pnpm add vitepress vue
mkdir -p .vitepress/theme .vitepress/public
```

## package.json

```json
{
  "name": "docs-site",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vitepress dev",
    "build": "vitepress build",
    "preview": "vitepress preview"
  },
  "devDependencies": {
    "vitepress": "^1.6.4"
  },
  "dependencies": {
    "vue": "^3.5.17"
  }
}
```

## VitePress 配置要点（config.mjs）

```javascript
import { defineConfig } from "vitepress";

export default defineConfig({
  title: "项目名",
  description: "项目描述",

  head: [
    ["link", { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
  ],

  themeConfig: {
    logo: "/logo.png",
    nav: [
      { text: "Home", link: "/" },
      { text: "文档", link: "/doc" },
    ],
    sidebar: [
      {
        text: "文档",
        items: [
          { text: "首页", link: "/" },
          { text: "架构", link: "/architecture" },
        ],
      },
    ],
    socialLinks: [
      { icon: "github", link: "https://github.com/user/repo" }
    ],
    footer: {
      message: "基于 xxx 开源项目构建",
      copyright: "Copyright © 2024-present xxx"
    },
  },

  // 关键：GitHub Pages 部署到子目录时必须匹配仓库名
  base: "/仓库名/",

  rewrites: {},
});
```

## 首页配置（index.md）

```markdown
---
layout: home

hero:
  name: "项目名"
  text: "项目描述"
  tagline: "基于 xxx 开源项目"
  image:
    src: /banner.png
    alt: Banner
  actions:
    - theme: brand
      text: 架构分析 →
      link: /architecture
    - theme: alt
      text: 插件开发 →
      link: /plugin-development

features:
  - icon: 🏗️
    title: 架构分析
    details: 9个核心模块、4种设计模式
    link: /architecture
---
```

## GitHub Actions 部署（deploy.yml）

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [master]
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
      url: https://user.github.io/repo/
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

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

## 关键注意事项

1. **config 必须 .mjs 扩展名** — VitePress 使用 ESM，`config.js` 会报错
2. **base 必须匹配仓库名** — 部署到 `https://user.github.io/repo/` 时，`base: "/repo/"`
3. **构建产物路径** — `docs-site/.vitepress/dist/`，deploy.yml 的 `upload-pages-artifact` path 要对应
4. **node 版本** — 推荐 Node 20，避免版本问题
5. **pnpm vs npm** — 锁定版本用 pnpm，workflow 中先装 pnpm 再 install

### deploy.yml 完整模板

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [master]
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
      url: https://user.github.io/repo/   # 替换为实际 URL
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

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

注意：`environment.url` 必须与 `base` 配置匹配，如 `base: "/claudecodesrc-design/"` 则 `url: https://yeluo45.github.io/claudecodesrc-design/`

## 本地预览

```bash
cd docs-site
pnpm install
pnpm run dev      # 开发预览
pnpm run build    # 生产构建
pnpm run preview  # 预览构建产物
```

## 已知问题

- VitePress 构建依赖 Vue 3，需同时安装 vue 依赖
- Windows WSL 环境下 pnpm 安装可能有权限问题，用 `npm install -g pnpm` 解决

## 重要教训

### git init 在已有 .git 时的行为

`git init` 在已有 `.git` 目录的目录中运行时，**不会报错**（exit 0），但实际上不会重新初始化。验证方式：

```bash
# 错误方式：依赖 exit code
cd /path/to/project && git init && git remote add origin ...  # 如果已有 .git，remote 不会添加成功

# 正确方式：先验证 git repo 是否真实存在
cd /path/to/project
git rev-parse --git-dir 2>/dev/null && echo "git repo exists" || echo "not a git repo"
```

### git remote add origin 的安全做法

```bash
# 会失败：如果是已初始化的 repo，remote 已存在
git remote add origin https://github.com/user/repo.git  # fatal: remote origin already exists.

# 正确方式：先检查或用 set-url
git remote -v | grep -q "^origin" && git remote set-url origin https://github.com/user/repo.git || git remote add origin https://github.com/user/repo.git
```

### git add -A + commit 在非 git 目录的行为

```bash
# 如果目录不是 git repo，commit 会失败
git add -A && git commit -m "..."  # exit code 128, fatal: not a git repository

# 正确顺序：
# 1. 先 git init
# 2. 验证 git rev-parse --is-inside-work-tree 返回 true
# 3. 再 git add + commit
```

### gh repo create 不要加 --source

```bash
# 错误：会在创建仓库后将本地 .git 的 origin 指向自己，报 "Unable to add remote origin"
gh repo create user/repo --public --source=/path/to/local

# 正确：先创建空仓库，再 push
gh repo create user/repo --public
cd /path/to/local && git push -u origin master
```

### git push 失败时的 Fallback：REST API 上传

当 `git push -u origin master` 因网络问题（HTTP 408、GnuTLS EOF、RPC failed）持续超时时，用 GitHub Contents API 上传：

```bash
# 单文件
gh api --method PUT "repos/{owner}/{repo}/contents/{path}" \
  -f content="$(base64 -w0 file.md | tr -d '\n')" \
  -f message="add file.md"
```

更新已存在文件必须先获取 sha，否则 422：

```python
import urllib.request, json, base64, subprocess

TOKEN = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip()
headers = {'Authorization': f'token {TOKEN}'}

def upload_file(repo, path, content):
    # 先获取现有 sha（更新时必须）
    get_req = urllib.request.Request(f'https://api.github.com/repos/{owner}/{repo}/contents/{path}',
                                     headers=headers)
    sha = None
    try:
        with urllib.request.urlopen(get_req, timeout=10) as r:
            sha = json.loads(r.read()).get('sha')
    except: pass

    payload = json.dumps({
        'message': f'add {path}',
        'content': base64.b64encode(content).decode(),
        **({} if not sha else {'sha': sha})
    }).encode()
    req = urllib.request.Request(url, data=payload, headers=headers, method='PUT')
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())
```

**注意**：API 有频率限制（5000 req/hour），大量文件上传会触发限流。

### pnpm workspace 会将 node_modules 跟踪进 git

pnpm monorepo 项目中，`git ls-files` 可能包含 4000+ 个 `node_modules` 文件，导致 push 时 RPC 超时。修复：

```bash
git rm -r --cached docs-site/node_modules
echo "docs-site/node_modules/" >> .gitignore
git add .gitignore && git commit -m "remove node_modules from tracking"
```

验证：`git ls-files | grep -c node_modules` 应为 0。

### README.md 必须包含远程仓库链接

每个 design 项目 README.md 应在标题后添加：

```markdown
# Project Name

Design documentation site for [SourceRepo](https://github.com/owner/source) — description.

**GitHub Repository**: https://github.com/yeluo45/project-name
```

并单独 commit 此更新（不要与初始 commit 合并）。
