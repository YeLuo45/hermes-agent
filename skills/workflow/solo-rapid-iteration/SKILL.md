---
name: solo-rapid-iteration
description: 单人高速迭代模式 — 单人维护 Web 应用（React/Vite）的快速原型→验证→部署迭代流程
tags: [workflow, react, vite, github-pages]
---

# Solo Rapid Iteration — 单人高速迭代模式

## 适用场景
单人维护的 Web 应用（React/Vite），需要快速原型 → 验证 → 部署的迭代循环。

## 核心特征
- 无 subagent，每个版本由协调者（小墨）独立完成
- 每个版本是独立 feature branch，合并 main 后 GitHub Actions 自动部署
- 版本用 URL query param `?v=N` 管理（`vite build` 时注入）
- 每个版本包含 1-3 个功能点，不要贪多
- 每次迭代后浏览器验证，再推进下一个

## 标准流程

### 1. 创建版本分支
```bash
git checkout main && git pull origin main
git checkout -b feature/v{N}-{short-description}
```

### 2. 创建提案文档
`~/.hermes/proposals/P-{date}-{seq}.md`
内容：概述、功能N描述（需求+技术方案）、验收标准、超时确认

### 3. 实现功能
- 新功能用 `write_file`
- 现有文件修改用 `patch`
- 每完成一个功能立即构建验证（`vite build`）

### 4. 提交推送
```bash
git add -A && git commit -m "feat: V{N} {描述}"
git push origin feature/v{N}-{short}
```

### 5. 合并部署
```bash
git checkout main && git merge feature/v{N}-{short} -m "merge: V{N} ..."
git push origin main
# 等待 GitHub Actions（约50-60s）
gh run list --repo {owner}/{repo} --limit 3
```

### 6. 浏览器验证 + 提案更新
- `browser_navigate` 验证 `?v={N+8}`（Actions deploy 会 +8）
- 更新 `proposal-index.md`：新提案插到最前，状态 delivered/accepted

## 版本号管理
- `vite.config.js` 的 `define` 中 `import.meta.env.VITE_VERSION` 控制版本号
- 每次 build 后手动 +1（或由 Actions workflow 自动递增）
- 当前部署版本 = `?v=` URL 参数，浏览器验证用

## 路径规范
- 代码：`/home/hermes/{project}/`
- 提案：`~/.hermes/proposals/`
- feature branch 命名：`feature/v{N}-{theme}`

## 关键约束
- 一次一个主题，不要在一个版本里混不相关的功能
- 构建失败立即修复，不要带着错误推进
- 浏览器验证是强制的，确保功能真正可用
- 提案超时后自动推进，不需要等待确认
