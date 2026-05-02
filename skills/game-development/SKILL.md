---
name: dbg-card-game-debug
description: DBG卡牌游戏调试方法论 - 浏览器缓存验证、subagent交付验收、常见坑点
tags: [game, debug, browser, cache, subagent]
version: 1.0
created: 2026-05-02
updated: 2026-05-02
---

# DBG Card Game Debug Skills

## 项目信息

- 项目: PRJ-20260421-001 DBG卡牌游戏
- 地址: /mnt/c/Users/YeZhimin/Desktop/card-game-prototype/index.html
- 部署: https://yeluo45.github.io/card-game-prototype/
- 分支策略: main (开发) → gh-pages (GitHub Pages镜像)
- 修复流程: 直接提交到 gh-pages，然后 cherry-pick 到 main

---

## 调试方法论

### 1. 验证浏览器加载的是最新代码

**问题症状**: `search_files` 确认代码存在，但 `browser_console` 报告函数 undefined

**原因**: 浏览器缓存了旧的 JavaScript

**解决方法**:

```
browser_navigate('https://.../?v=5')  // 任何查询参数都有效，强制刷新
```

**验证代码**:

```javascript
// 检查函数是否在 window 上（全局作用域）
window.showRewardScreen ? 'exists' : 'missing'

// 注意：内部函数不在 window 上，只能通过行为验证
```

### 2. 验证实际行为而非代码状态

**错误方法**: 只看代码有没有

```javascript
// 不可靠：代码在文件里不等于浏览器执行了
grep "function showRewardScreen" index.html
```

**正确方法**: 模拟真实流程测试

```javascript
// 设置完整状态
gameState.currentNode = { type: 'combat', ... }
gameState.enemyHp = 0

// 触发目标函数
checkEnemyDeath()

// 验证结果
document.getElementById('overlay').classList.contains('show')
```

### 3. Subagent 交付验收清单

Dev agent 完成后必须逐项验证：

| 验证项 | 方法 |
|--------|------|
| 函数存在 | `browser_console` 中检查 `typeof functionName` |
| 函数在 window 上 | `window.functionName ? 'exists' : 'missing'` |
| 界面元素存在 | `document.getElementById('element-id') ? 'exists' : 'missing'` |
| 完整流程 | 模拟触发条件，检查 UI 变化 |
| 数据正确性 | `gameState` 相关字段变化 |

---

## 常见问题模式

### 诅咒/特殊效果未触发

- 原因: `triggerCurseEffect()` 未接入 `startPlayerTurn`
- 验证: `gameState.curses` 有值但回合开始无日志

### 第二层无法点击节点

- 原因: `unlockedNodes` 为空数组，未初始化新楼层节点
- 验证: `gameState.unlockedNodes` 在进入新楼层后是 `[]`
- 修复: `checkEnemyDeath()` 中楼层切换时添加起点节点解锁逻辑

### 奖励界面不显示

- 原因1: `showRewardScreen` 函数名不匹配（dev agent 用了不同名称）
- 原因2: `checkEnemyDeath` 中调用了不存在的函数
- 验证: `typeof showRewardScreen` vs `typeof showRewardSelection`

---

## Git 修复工作流

```bash
# 在 gh-pages 上修复
git checkout gh-pages
# 修改代码
git add -A && git commit -m "fix: 描述"
git push origin gh-pages

# 同步到 main
git checkout main
git cherry-pick <commit-hash>
git push origin main

# 合并回 gh-pages（保持同步）
git checkout gh-pages
git merge main -m "Merge main into gh-pages"
git push origin gh-pages
```

---

## 关键文件位置（截至 V5）

| 功能 | 位置 |
|------|------|
| 卡牌数据 | 约 line 505-670 |
| gameState 初始化 | 约 line 650-690 |
| startPlayerTurn | 约 line 1050-1100 |
| checkEnemyDeath | 约 line 1700+ |
| returnToMap | 约 line 1730+ |
| 奖励相关函数 | 约 line 1700+ |
| 地图渲染 | 约 line 1100-1200 |

---

## 已知坑点

1. **V4 dev agent 交付不完整**: `poisonStacks`/`bleedStacks` 未初始化，中毒/流血未实现。需要手动补全。
2. **提案索引重复条目**: `patch` 时 old_string 要足够唯一，否则匹配多处导致重复。
3. **浏览器缓存**: 每次代码更新后用 `?v=N` 强制刷新验证。
