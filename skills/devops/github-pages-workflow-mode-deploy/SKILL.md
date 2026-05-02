---
name: github-pages-workflow-mode-deploy
description: GitHub Pages workflow mode deployment — switching from legacy to Actions-based build, avoiding gh-pages force-push mistakes
---

# GitHub Pages Workflow Mode 部署

## 背景
GitHub Pages 有两种构建模式：
- **legacy（静态站点）**：从指定分支的源码目录读取，GitHub Pages 自动构建。不读取 gh-pages 分支内容。
- **workflow（Actions）**：通过 GitHub Actions workflow 管理部署，workflow 负责构建并推送到指定分支。

legacy 模式下直接 push dist 到 gh-pages 分支是无效的——GitHub Pages 根本不从那里读取。

## 识别当前模式
```bash
gh api repos/{owner}/{repo}/pages
# 查看 build_type 字段
```

## 切换到 workflow 模式
```bash
gh api repos/{owner}/{repo}/pages --method PUT --input - <<'EOF'
{"source":{"branch":"main","path":"/","build_type":"workflow"}}
EOF
```

## 标准 workflow（peaceiris/actions-gh-pages）
```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm ci
      - name: Build
        run: npm run build
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

## 常见坑
1. **gh-pages 分支被 legacy 构建覆盖**：legacy 模式下 GitHub Pages 从源码构建后会自动更新 gh-pages，force-push 到 gh-pages 会被下次构建覆盖。
2. **workflow 没有写入权限**：必须添加 `permissions: contents: write`。
3. **vite base 路径**：部署到子目录（如 `/todo-list/`）时，需要确保 `vite.config.js` 的 `base: '/todo-list/'` 正确，且 HTML 中的资源路径也指向子目录。

## 验证
```bash
# 检查 Pages 配置
gh api repos/{owner}/{repo}/pages

# 检查最新的 deployment
gh run list --repo {owner}/{repo} --limit 5

# 验证页面资源路径
curl -s https://{owner}.github.io/{repo}/ | grep -o 'src="[^"]*"'
```

## 关键经验
- legacy 模式下 gh-pages 分支不可靠，应该完全依赖 GitHub Pages 的自动构建。
- workflow 模式下 gh-pages 由 action 管理，不要手动 force-push 到该分支。
- 部署失败时，先确认 build_type 是否正确切换到了 workflow。
- **永远不要让 legacy build 和 workflow build 同时运行**：legacy 的 `pages build and deployment` workflow 会和自定义 workflow 互相覆盖 gh-pages，导致 404。如果两种模式冲突，先用 `build_type=workflow` 切换，然后用 workflow 唯一负责部署。
- **切换 build_type 必须用 `--input -` + JSON stdin**：`-F` flags 会导致 build_type 被静默忽略，始终保持 legacy。
- **artifact serving**：workflow mode 的 Pages 部署通过 artifact 系统，不直接操作 gh-pages 可见的 blob，但最终通过 `https://{user}.github.io/{repo}/` 可访问。
