---
name: dbg-card-game-workflow
description: PRJ-20260421-001 DBG卡牌游戏标准化开发流程 - PRD起草→dev agent委托→验收→部署
---

# DBG 卡牌游戏开发流程

## 概述
PRJ-20260421-001 DBG卡牌游戏的标准化开发流程。

## 标准迭代流程

1. **起草 PRD** → `workspace-pm/proposals/P-YYYYMMDD-NNN-prd.md`
2. **更新 proposal-index.md** → `approved_for_dev` + `confirmed`
3. **委托 dev agent** → `delegate_task`，传 PRD 路径 + 游戏文件路径
4. **Dev 完成检查** → `git log --oneline origin/gh-pages -3` 确认 commit 存在
5. **验收** → browser 验证功能，console 检查关键函数
6. **更新 proposal-index.md** → `accepted` + dev commit hash
7. **询问 boss** → 是否继续下一迭代

## Dev Agent 委托模板

```
项目路径: /mnt/c/Users/YeZhimin/Desktop/card-game-prototype/index.html
PRD: /home/hermes/.hermes/proposals/workspace-pm/proposals/P-XXXXXXXX-XXX-prd.md
GitHub Token: (见记忆文件中的 gh_token)
```

## 关键检查点

### 验证部署成功
```bash
git log --oneline origin/gh-pages -1
```
输出包含版本号和内容说明即成功。

### 验证功能存在
```javascript
// browser console
typeof functionName !== 'undefined'
Object.keys(RELICS || {}).length
FLOORS.length
```

### GitHub Pages 缓存刷新
```
https://yeluo45.github.io/card-game-prototype/?t=1746288000
```
时间戳每次不同即可。

## 常见问题

### Dev agent 未完成 git push
当 dev agent 用 max_iterations 限制时，可能在 git push 前达到上限。
**处理**：检查 `git status --short`，如有修改则手动 commit + push。

### Merge conflict（单文件项目）
```bash
git checkout --theirs index.html  # 取 subagent 的新版本
git add index.html
git commit -m "resolve merge conflict"
```
单文件 HTML 游戏没有复杂合并冲突，直接取新版本安全。

### 浏览器显示旧版本
- 用 `?v=N` 或 `?t=timestamp` 强制刷新
- 检查 HTML `<title>` 确认实际版本

## 版本历史

| 版本 | 提案 | 主要内容 |
|------|------|----------|
| V1 | P-20250421-001 | 核心战斗循环 |
| V2 | P-20260502-003 | 卡牌扩充 + 敌人扩充 |
| V3 | P-20260502-006 | 地图/进度系统 |
| V4 | P-20260502-011 | 诅咒牌与特殊牌系统 |
| V5 | P-20260502-012 | 战斗奖励卡牌选择系统 |
| V6 | P-20260502-013 | 遗物/神器系统 |
| V7 | P-20260502-015 | 敌人与Boss扩充 |
| V8 | P-20260502-016 | 卡牌升级系统 |
| V9 | P-20260503-001 | 成就系统 |
| V10 | P-20260503-002 | 章节扩展（第4/5层） |
| V11 | P-20260503-003 | 更多遗物效果 |
| V12 | P-20260503-004 | 音效与特效 |

## 游戏访问
https://yeluo45.github.io/card-game-prototype/
