---
name: todo-list-versioning
description: Hermes TodoList PRJ-20260421-001 的高速迭代模式 — ?v=N 版本管理、proposal-index.md 维护、GitHub Actions 部署流程
category: productivity
tags: [react, vite, github-pages, rapid-iteration]
---

# TodoList 版本迭代模式

## 概述

Hermes TodoList (PRJ-20260421-001) 采用 `?v=N` 查询参数 + proposal-index.md 的高速迭代模式。每次功能迭代递增版本号，构建后 GitHub Actions 自动部署。

## 核心约定

### 版本号
- 当前版本：`?v=26`（V18）
- 每次迭代递增 1（V16→V17→V18...）
- 访问地址：`https://yeluo45.github.io/todo-list/?v=N`

### Git 分支策略
- `main`：稳定版本（直接部署到 GitHub Pages）
- `feature/vN-xxx`：功能分支，完成后 merge 到 main
- 合并后 GitHub Actions 自动触发构建部署（约 1-2 分钟）

### 迭代流程（每次功能迭代）
1. `git pull origin main`
2. `git checkout -b feature/vN-feature-name`
3. 实现功能 + 构建验证 `vite build`
4. `git add -A && git commit -m "feat: V$N 功能描述"`
5. `git push origin feature/vN-feature-name`
6. `git checkout main && git merge feature/vN-feature-name -m "merge: V$N 功能描述"`
7. `git push origin main`
8. 等待 55-60 秒后 `gh run list --repo YeLuo45/todo-list --limit 3` 确认部署成功
9. 更新 `~/.hermes/proposals/proposal-index.md`：在该版本之前的条目（V15）插入新版本条目
10. 浏览器验证 `https://yeluo45.github.io/todo-list/?v=N`

### proposal-index.md 更新方式（Python 脚本）
```python
content = open('/home/hermes/.hermes/proposals/proposal-index.md').read()
v15_pos = content.find('### P-20260503-023: TodoList V15')
last_up = content.find('- `Last Update`: 2026-05-03', v15_pos)
sep = content.find('\n---\n', last_up)

v_new = '''- `Last Update`: 2026-05-03

---

### P-YYYYMMDD-NNN: TodoList VN — 功能名

- `Proposal ID`: `P-YYYYMMDD-NNN`
- `Title`: TodoList VN — 功能名
- `Owner`: 小墨
- `Current Status`: delivered
- `Stage`: VN Iteration
- `Acceptance`: accepted
- `Notes`: 关键功能亮点
- `Last Update`: 2026-05-03

'''

new_content = content[:last_up] + v_new + content[sep+5:]
open('/home/hermes/.hermes/proposals/proposal-index.md', 'w').write(new_content)
```

## TodoList 项目结构

- 工作目录：`/home/hermes/todo-list/`
- 源码：`src/`（React + Vite）
- 工具函数：`src/utils/`（gistSync.js, projects.js, reminder.js）
- 组件：`src/components/`（TaskList.jsx, KanbanBoard.jsx, GanttChart.jsx, FilterBar.jsx, ProjectSidebar.jsx, GistSyncModal.jsx 等）
- GitHub 仓库：`YeLuo45/todo-list`
- 构建命令：`/home/hermes/.npm-global/bin/vite build`

## 关键组件关系

- `App.jsx`：主容器，管理视图切换（dashboard/list/kanban/gantt）
- `TaskContext.jsx`：全局任务状态（tasks, filterTags, filterProject, searchQuery, sortBy, hideCompleted, dateFilter）
- `GistSync.jsx`：GitHub Gist 同步（已实现自动备份）
- `GistSyncModal.jsx`：Gist 同步/备份弹窗（双 Tab：同步设置 + 备份与恢复）
- `ProjectSidebar.jsx`：左侧项目树形边栏（可折叠，管理弹窗）
- `FilterBar.jsx`：搜索栏 + 排序 + 标签过滤（支持标签组、批量重命名、标签统计）
- `GanttChart.jsx`：甘特图（三视图：月/周/资源）

## 常用模式

### 添加新功能到 GanttChart
```javascript
// 在 GanttChart.jsx 中添加 viewMode 状态
const [viewMode, setViewMode] = useState('month'); // 'month' | 'week' | 'resource'
const DAY_WIDTH = viewMode === 'week' ? 80 : viewMode === 'resource' ? 60 : 40;

// 添加切换按钮
<button className={`gantt-group-btn ${viewMode === 'resource' ? 'active' : ''}`}
  onClick={() => setViewMode('resource')}>📊 资源</button>

// 在 gantt-body 之前渲染新视图
{viewMode === 'resource' && (
  <ResourceView tasks={tasks} days={days} ... />
)}
```

### 添加全局状态到 TaskContext
1. `useState` 添加状态变量
2. `allTasks` 的 `filter()` 中添加过滤逻辑
3. `context value` 对象中添加 `{ state, setState }`

### 工具函数模块（projects.js 模式）
```javascript
const STORAGE_KEY = 'hermes-xxx-v1';
export function getXxx() { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
export function saveXxx(data) { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); }
export function createXxx(...) { /* 创建对象，添加到数组，保存 */ }
export function updateXxx(id, updates) { /* 查找并更新 */ }
export function deleteXxx(id) { /* 过滤删除 */ }
```

## GitHub Actions 部署

- 触发条件：`push` 到 `main` 分支
- 构建：`npm ci && npm run build`
- 部署：自动部署 `dist/` 到 GitHub Pages
- 状态检查：`gh run list --repo YeLuo45/todo-list --limit 3`

## 记忆要点

- 构建：`/home/hermes/.npm-global/bin/vite build`（不是 `npm run build`，避免路径问题）
- V17 后 App.jsx 在列表视图左侧添加了 ProjectSidebar（不影响看板/甘特图）
- FilterBar 重写了标签系统（标签组、多选批量重命名、标签统计）
- GistSyncModal 有两个版本：旧版（同步）+ 新版（同步+备份恢复双Tab）
- 提案系统根目录：`~/.hermes/proposals/`
- 提案索引：`~/.hermes/proposals/proposal-index.md`
- 新提案格式：`P-YYYYMMDD-NNN.md`
