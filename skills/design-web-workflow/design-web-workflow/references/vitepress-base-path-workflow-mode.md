# VitePress Base Path: Workflow Mode vs Subdirectory Deploy

> 2026-05-14 — autoagent-design 项目教训

## 核心问题

workflow mode GitHub Pages 部署时，artifact 直接部署到 `https://username.github.io/` 根路径，而不是 `https://username.github.io/repo-name/`。

| 部署模式 | base 配置 | 实际 URL |
|----------|-----------|----------|
| gh-pages branch + peaceiris/actions-gh-pages | `/repo-name/` | `/repo-name/` ✓ |
| workflow mode (actions/deploy-pages) | `/` | `/` ✓ |
| workflow mode (错误配置) | `/repo-name/` | `/repo-name/` ✗ 404 |

## autoagent-design 错误配置

```js
// ❌ 错误 — workflow mode 下会导致所有链接指向 /autoagent-design/ 但资源在 /
base: "/autoagent-design/",
```

症状：
- `https://yeluo45.github.io/autoagent-design/` → 404
- JS/CSS 资源加载正常（相对路径正确）
- VitePress SPA 路由无法工作

## 正确配置

```js
// ✅ 正确 — workflow mode 直接部署到根
base: "/",
```

## 判断规则

| 场景 | base 配置 |
|------|-----------|
| GitHub Pages 子目录 (`/repo-name/`) + gh-pages action | `/repo-name/` |
| GitHub Pages 根路径 (`/`) + workflow mode | `/` |

## 相关案例

| 项目 | 部署方式 | base | 结果 |
|------|----------|------|------|
| bmad-method-design | workflow mode | `/bmad-method-design/` | ✗ 404 |
| autoagent-design | workflow mode | `/` | ✓ |

## 快速修复

1. 修改 `.vitepress/config.mjs`：`base: "/"`
2. 推送 → GitHub Actions 重新构建
