---
name: ai-novel-assistant-iteration-workflow
description: ai-novel-assistant 项目从 PRD 到交付的高速迭代流程 — 多Agent协作写作助手，V12-V19迭代经验
---

# ai-novel-assistant 高速迭代工作流

## 项目概述

GitHub: https://github.com/YeLuo45/ai-novel-assistant
技术栈: React 18 + Vite 5 + TypeScript + PWA
工作目录: `/home/hermes/.hermes/proposals/workspace-dev/proposals/ai-novel-assistant/`
构建命令: `npm run build`

## 核心架构

### Agent系统 (V12+)
- `src/ai/collaboration/` — 协作编排器、任务分解、冲突解决
- `src/ai/agents/` — PlotExpert, DialogueMaster, StyleGuard, CriticAgent
- `src/ai/memory/` — 跨章节记忆系统 (V14)
- `src/ai/genres/` — 类型优化 (V15)
- `src/ai/versioning/` — 多版本生成 (V16)
- `src/ai/intervention/` — 实时干预机制 (V17)
- `src/ai/materials/` — 素材库 (V18)

### UI组件 (V12+)
- `src/components/WritingEditor.tsx` — 主编辑组件
- `src/components/CollaborationVisualizer.tsx` — 协作可视化
- `src/components/InterventionStatusBar.tsx` — 干预状态栏
- `src/components/MaterialLibraryPanel.tsx` — 素材库面板

## 核心流程（每迭代约 8-10 分钟）

### Step 1: 方向确认
boss 从 A/B/C/D/E 选项中选取方向（A/B/D/E 已定义）。

### Step 2: PRD 起草
- 路径: `/home/hermes/proposals/PRJ-YYYYMMDD-NNN.md`
- 内容: 需求概述 + 核心设计 + 类型定义 + 实现计划 + 验收标准
- 状态: `prd_pending_confirmation`

### Step 3: 提案登记
- 路径: `/home/hermes/proposals/proposal-index.md`
- 新条目添加到末尾
- 状态: `prd_pending_confirmation`

### Step 4: boss 确认 "确认"
直接继续 Step 5，不等待。

### Step 5: 委托 dev agent（Phase 1-2 先行）
传递:
- PRD 内容摘要
- 项目路径
- Phase 1-2 任务列表（核心类型/存储/引擎）
- 构建命令
- 验收标准

### Step 6: Phase 1-2 完成 → 委托 Phase 3-4
- Phase 1-2 完成后立即委托 Phase 3-4
- UI组件 + WritingEditor集成

### Step 7: 验收检查
```bash
cd /home/hermes/.hermes/proposals/workspace-dev/proposals/ai-novel-assistant
npm run build  # 验证构建成功
git add -A && git commit -m "feat: VXX description (Phase 1-4)" && git push
```

### Step 8: 更新提案登记
- 状态: `delivered`

---

## 关键教训

### 提案路径
- **提案根目录**: `/home/hermes/proposals/`（不是 `~/.hermes/proposals`）
- **PRD文件**: `/home/hermes/proposals/PRJ-YYYYMMDD-NNN.md`
- **索引文件**: `/home/hermes/proposals/proposal-index.md`

### patch 唯一性
更新 proposal-index.md 时，old_string 必须包含至少 2 行上下文确保唯一性：
```
| P-20260513-002 | ai-novel-assistant | delivered | V16 多版本...
```
不要只匹配 `| P-20260513-002 |` — 会匹配到多个条目。

### 委托批次
- Phase 1-2（核心引擎）先委托，约 5 分钟完成
- Phase 3-4（UI+集成）后委托，约 3 分钟完成
- 总计约 8-10 分钟完成一个迭代

### subagent 失败模式
- 常见: subagent hit max_iterations 在 commit 之前
- 预防: 每次都检查 `git status`，未提交则手动 commit
- 验证: `git log --oneline -2` 确认 commit 在正确分支

### WritingEditor 集成模式
新增功能通常需要:
1. 在 WritingEditor.tsx 中添加 import
2. 添加 state（如 `showMaterialLibrary`, `executionStatus`）
3. 添加 Tab 切换按钮
4. 添加功能面板/Modal
5. 在 handleCollaboration 中注入上下文

---

## 迭代历史

| 版本 | 核心功能 |
|------|----------|
| V12 | 多Agent协作引擎 |
| V13 | Agent能力深化（CriticAgent） |
| V14 | 跨章节记忆系统 |
| V15 | 类型垂直优化（悬疑/言情/科幻/同人） |
| V16 | 多版本生成与对比 |
| V17 | 实时干预机制 |
| V18 | 写作素材库集成 |
| V19 | 协作效率优化（进行中） |

---

## 快捷查询

- 当前进度: `git log --oneline -5`
- 构建状态: `npm run build 2>&1 | tail -5`
- 文件追踪: `git status --short`