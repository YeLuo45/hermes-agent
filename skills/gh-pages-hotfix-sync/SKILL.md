---
name: gh-pages-hotfix-sync
description: gh-pages与main分支同步问题排查与修复 — 双向同步场景
category: github
---

# gh-pages 与 main 分支同步

## 常见问题

### 场景A：热修复后同步源码到 main（现有流程）
直接 patch gh-pages 紧急上线后，main 源码分支未同步。下次构建会覆盖热修复。

### 场景B：main 已更新但 GitHub Pages 没变化（本次问题）
dev push 到 main 后 GitHub Pages 仍显示旧版本。因为 GitHub Pages 部署的是 gh-pages 分支，不是 main。

## 场景B 排查流程

1. 发现问题：push 到 main 后 GitHub Pages 没更新
2. 检查远程分支：
```bash
git ls-remote --heads origin
```
3. 如果看到 `gh-pages` 分支存在，说明 GitHub Pages 部署的是 gh-pages
4. 检查 gh-pages 是否落后：
```bash
git fetch origin gh-pages:gh-pages
git log gh-pages --oneline -5
git log main --oneline -5
```
5. 确认问题：gh-pages 落后 main 很多提交

## 场景B 修复流程

```bash
git checkout gh-pages
git merge main --allow-unrelated-histories -m "Merge from main"
# 如果有冲突，用 --theirs 保留 main 版本
git checkout --theirs index.html
git add index.html
git commit -m "Sync to gh-pages"
git push origin gh-pages
git checkout main
```

## 关键判断
- GitHub Pages 部署源可能是 `gh-pages` 分支或 `main` 分支（取决于仓库设置）
- 如果是 gh-pages 分支，push 到 main 不会自动更新 GitHub Pages
- 需要手动同步 main 到 gh-pages

## 验证命令
```bash
# 检查 gh-pages 结构
git ls-tree gh-pages

# 检查当前加载的页面标题（确认是否最新版本）
curl -s https://username.github.io/repo/ | grep '<title>'

# 强制刷新
curl -s "https://username.github.io/repo/?t=$(date +%s)"
```
