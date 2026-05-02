---
name: proposal-todolist
description: 提案系统的 TodoList 功能 — 在 proposal-index.md 中管理待办项，作为轻量级任务跟踪系统
---

# Proposal TodoList Skill

## 概述

提案系统内置 TodoList 功能，通过 `todo` 工具管理。Todo 项以结构化格式存储在 `~/.hermes/proposals/proposal-index.md` 文件末尾，作为持久化待办清单。

## TodoList 格式

```
## Todo

- [ ] 待办项1 — 描述
- [x] 已完成项 — 描述
```

格式规则：
- `## Todo` 标题标记 TodoList 区域
- `[ ]` 未完成，`[x]` 已完成
- 每个 Todo 项一行，以 `—` 分隔标题和描述
- 按创建顺序排列，最新在上

## 工具使用

### 查看所有 Todo
```
todo(action='list')
```

### 添加 Todo
```
todo(action='add', title='标题', description='描述', due='YYYY-MM-DD')
```
- `title`: 必填，简洁标题（建议 20 字以内）
- `description`: 可选，详细描述
- `due`: 可选，截止日期

### 标记完成
```
todo(action='complete', id='todo-id')
```

### 删除 Todo
```
todo(action='remove', id='todo-id')
```

### 更新 Todo
```
todo(action='update', id='todo-id', title='新标题', description='新描述')
```

## 与 proposal-index.md 的关系

- TodoList 存储在 `~/.hermes/proposals/proposal-index.md` 末尾
- 每次修改后自动同步到文件
- Todo 不属于任何特定提案，是全局任务清单
- 定时同步脚本（cron）不会将 Todo 项推送到 GitHub proposals.json

## 用途

- 跟踪跨提案的技术债务
- 记录需要 boss 确认的事项
- 管理部署后的验证任务
- 记录网络恢复后的待执行操作

## 示例

```
## Todo

- [ ] P-20260422-002-sync — 网络恢复后推送 proposals.json 到 proposals-manager
- [ ] P-20260422-002-verify — 验证 Soul Shooter 出现在 proposals-manager 网站
```

## 倒计时规则

PRD/技术期望确认采用倒计时自动推进机制：
- 说完话后立即创建 cron job，不能只说不做
- cron job 创建后 deliver=local，到期自动更新 proposal-index.md 状态

**schedule 参数格式（已验证）：**
- ISO timestamp（正确）：`2026-05-02T00:45:00`
- Duration 格式（错误）：`"in 5 minutes"` 会报错 "Invalid schedule"

```python
# 正确示例
cronjob(action='create', schedule='2026-05-02T00:45:00', ...)

# 错误示例（报错）
cronjob(action='create', schedule='in 5 minutes', ...)  # Invalid schedule
```

## 已知限制

- Todo 工具不支持子任务（无层级结构）
- 不支持标签、负责人、优先级字段
- 不支持排序，默认按创建顺序
