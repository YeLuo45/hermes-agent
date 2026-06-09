# sync-proposals-to-website.py 分组逻辑陷阱

> **发现日期**: 2026-05-14

## 问题描述

`sync-proposals-to-website.py` 脚本在将提案数据同步到 GitHub 时使用 `projectName` 字段进行项目分组。以下逻辑陷阱可能导致孤儿项目和错误的提案数量。

## 陷阱清单

### 1. Project 字段中文名优先分组

`Project` 字段中文名优先用于分组，而非使用 PRJ ID。这导致：
- 同一个项目可能因为中文名称不一致而被分成多个组
- 英文名和中文名指向同一项目却无法合并

### 2. p-* 开头 ID 永远不分组

代码中有以下逻辑：
```python
# p-* 开头是垃圾数据（分组失败产物），直接跳过
if proj_name.startswith('p-'):
    continue
```
但问题是：**这些 `p-*` 开头的数据是分组失败的产物，说明原始分组逻辑有问题**。

### 3. Fallback 逻辑错误导致孤儿项目

错误逻辑：
```
if Project 字段为空且不是 PRJ- 格式 → 跳过该提案（正确）
有效项目但 Project 字段为空 → 跳过（不创建孤儿）（正确）
```

但实际代码中，当无法从 `Project` 字段提取 PRJ ID 时，会 fallback 到 `name`（从 GitHub Repo 推断），这个推断的名称可能与实际项目名不符。

### 4. 中文顿号 `、` 破坏 group_by

当项目名含中文顿号 `、` 时（如 `ai-stock、ai-subscription`），split 操作会产生错误字段：

```python
# 问题代码
parts = project_path.rstrip("/").split("/")
name = parts[-1]  # 如果 path 含有括号，这里可能取到错误的部分

# 当 project_field 为 "PRJ-xxx（ai-stock、ai-subscription）" 时
# split('、') 可能产生: ["PRJ-xxx（ai-stock", "ai-subscription）"]
# 导致项目 ID 被污染为 "ai-subscription）on"
```

## 正确逻辑

```python
# 1. 优先使用 PRJ ID 作为分组 key
prj_id_match = re.search(r'(PRJ-\d{8}-\d{3})', project_field)
prj_id = prj_id_match.group(1) if prj_id_match else ''

# 2. 只有当 PRJ ID 存在时才分组
# 3. projectName 用于显示，不应影响分组逻辑
project_name_for_grouping = prj_id if prj_id else (name or pid)

# 4. p-* 开头的条目应该被过滤掉，而不是保留
# 5. 含顿号的项目名需要先清理
```

## 影响范围

- proposals.csv 中的 `project_name` 字段可能不正确
- proposals.json 中的 `projectName` 字段可能有孤儿
- 项目提案数量统计可能错误
- 网站显示的项目列表可能不完整或重复

## 修复建议

1. 在 `consolidate_related_projects()` 之后，增加 `p-*` 前缀过滤
2. 清理含特殊字符的项目名（中文顿号、括号等）
3. 确保分组逻辑始终以 PRJ ID 为准
4. 同步后增加一致性校验：本地提案数 == proposals.json 中的提案数

## 相关代码位置

- `/home/hermes/.hermes/scripts/sync-proposals-to-website.py`
- 分组逻辑：`read_local_proposals()` 函数，约第 170-180 行
- 过滤逻辑：`consolidate_related_projects()` 函数，约第 596-603 行
