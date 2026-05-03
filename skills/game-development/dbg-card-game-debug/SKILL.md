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

## 关键文件位置（截至 V6）

| 功能 | 位置 |
|------|------|
| gameState 初始化 | ~657 |
| startPlayerTurn (DOT结算) | ~1108-1120 |
| executeEnemyIntent (敌人中毒结算) | ~1452+ |
| startCombat | ~1065 |
| checkEnemyDeath | ~1576 |
| showRewardScreen | ~1702 |
| selectReward | ~1729 |
| skipReward | ~1737 |
| returnToMap | ~1730 |
| showRewardSelection | ~1744 |
| reward-overlay HTML | ~503 |

---

## 地图系统关键逻辑

### 起点节点判断（无入边）
```javascript
// 在 FLOORS[floorIndex].edges 中，查找没有任何边的第二个位置指向该节点
const hasIncoming = FLOORS[floorIndex].edges.some(([a, b]) => b === node.id);
if (!hasIncoming) unlockNode(node.id);
```

### 第二层起点节点（实际验证）
```
f2s1 (商店) - 无入边 → 解锁
f2r1 (休息) - 无入边 → 解锁
f2e1/f2c1/f2c2/f2c3/f2b1 - 有入边 → 未解锁
```

### 楼层切换完整流程（checkEnemyDeath）
1. 敌人HP≤0
2. 判断是否Boss/精英，可能获得诅咒牌（30%）
3. 延迟800ms显示奖励界面
4. completeNode() 完成节点
5. 判断楼层≥3则胜利，否则 currentFloor++ 并初始化新楼层解锁节点
6. returnToMap() 返回地图

---

## Dev Agent 交付验证清单（增强版）

1. 浏览器加载最新版本（加 ?v=N）
2. 检测关键函数是否存在（`typeof functionName`）
3. 检测 gameState 相关字段（`Object.keys(gameState).filter(k => k.includes('keyword'))`）
4. 手动触发核心逻辑验证行为
5. 验证 UI 更新（DOM 元素存在性、classList 变化）
6. 验证 gameState 状态变化
7. 完整流程走查（如：击败敌人 → 奖励界面 → 选择 → 牌组增加）

---

## 已知坑点

1. **V4 dev agent 交付不完整**: `poisonStacks`/`bleedStacks` 未初始化，中毒/流血未实现。需要手动补全。
2. **提案索引重复条目**: `patch` 时 old_string 要足够唯一，否则匹配多处导致重复。
3. **浏览器缓存**: 每次代码更新后用 `?v=N` 强制刷新验证。
4. **第二层解锁节点为空**: `returnToMap()` 不初始化新楼层，`checkEnemyDeath()` 楼层切换时必须初始化解锁节点。
5. **函数命名差异**: dev agent 可能使用不同函数名（如 `showRewardSelection` vs `showRewardScreen`），需要实际测试而非只看预期名称。
6. **遗物UI显示缺失**: V6 dev agent 实现了核心功能但 `relic-display` DOM 未添加，需要检查 `document.getElementById('relic-icons')` 验证。

## 关键教训（2026-05-03 新增）

**V5 致命错误**：V5 (P-20260502-012) 的 `showRewardScreen` 和 `selectReward` commit 了，提案标记为 "accepted"，但**从未集成到游戏流程**。验收时只检查了 git log，没有验证实际行为。

**后果**：DBG 核心功能"牌组构建"在 V5 到 V12 期间完全不可用，副标题"构建你的牌组"是空头承诺。直到 V13 才发现问题。

**正确做法**：
1. 每次 subagent 交付后，必须在浏览器中**实际触发核心功能**验证
2. 不能只看 `grep` 代码存在就标记 accepted
3. DBG 核心路径：start game → battle → defeat enemy → **奖励选择界面必须弹出**
4. 验证命令：`browser_console` 中检查 `typeof showCardReward` 和 `gameState.deck.length` 变化
