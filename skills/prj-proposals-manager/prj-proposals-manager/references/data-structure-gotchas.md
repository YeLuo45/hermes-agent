# prj-proposals-manager 数据结构坑点

## 两套数据源的对齐问题

### CSV 侧（结构化存储）

| 文件 | 主键格式 | 说明 |
|------|---------|------|
| `proposals.csv` | `P-YYYYMMDD-XXX` | `project_id` 是 `PRJ-YYYYMMDD-XXX` |
| `projects.csv` | `PRJ-YYYYMMDD-XXX` | `name` 是纯英文项目名 |
| `project_proposal_mapping.csv` | `PRJ-YYYYMMDD-XXX` ↔ `P-YYYYMMDD-XXX` | 关联表 |

**关键字段名对应：**

| 正确字段 | 错误字段（易混淆） |
|---------|------------------|
| `project_id` (PRJ-*) | `projectId`（camelCase，JS/JSON 侧） |
| `project_name` (英文) | `name`（项目自己的 name vs 提案自己的 name） |
| `prj_url` (CSV) | `deployment_url`（旧字段名，已废弃） |
| `prjUrl` (JSON) | `deploymentUrl`（旧字段名，已废弃） |

### Website JSON 侧（v2 树格式）

```json
{
  "version": 2,
  "projects": [
    {
      "id": "PRJ-20260510-001",       // 来自 projects.csv id
      "name": "ai-subscription",       // 来自 projects.csv name（英文）
      "description": "...",
      "url": "https://...",            // 来自 proposals.csv deployment_url
      "gitRepo": "https://github.com/...",
      "proposals": [
        {
          "id": "P-20260510-001",      // 提案自己的 id
          "name": "some feature",       // 提案自己的 name
          "projectId": "PRJ-20260510-001",
          "projectName": "ai-subscription",
          ...
        }
      ]
    }
  ]
}
```

### 常见坑

#### 坑1：同步脚本分组 key 用错字段

同步脚本 `sync-proposals-to-website.py` 中，若分组逻辑使用 `project_id` 匹配 `projects.csv`，但 CSV 中 `project_id` 格式与 `projects.csv` 的 `id` 格式不匹配，就会把提案自己的 `P-*` id 当作项目 id，产生大量垃圾项目（如 `p-20260509-002`）。

**正确做法**：按 `project_name` 分组，因为 `projects.csv` 的 `name` 字段与 `proposals.csv` 的 `project_name` 字段值一致（都是英文项目名）。

#### 坑2：project.name 混入中文

`projects.csv` 的 `name` 应该是英文。若同步脚本从提案 title 提取项目名，会混入中文。

#### 坑3：url/gitRepo 在项目层级缺失

`proposals.csv` 的 `deployment_url` 和 `git_repo` 是提案级字段。同步到网站 JSON 时，需要**提升**到 project 层级（取该项目的第一个非空值），因为项目卡片（SwimlaneRow）需要展示。

#### 坑4：ProjectDetailPage 和 KanbanView 数据流不一致

- `ProjectDetailPage` → 有 `ProjectInfo` 组件（支持编辑 url/gitRepo）
- `KanbanSwimlanes/SwimlaneRow` → 项目头部**没有** url/gitRepo 展示，也没有编辑入口

这是组件间的不一致：同一个数据在两个视图中的可见性不同。

#### 坑5：网站前端 ProjectCard 字段名（2026-05-15 已修复）

**问题现象**：proposals.json 数据正确（prjUrl 有值），但项目卡片不显示"访问"按钮。

**根因**：React 组件 `ProjectCard.jsx` 读取的字段名与 JSON 输出字段名不匹配。

| JSON 字段（sync 输出） | React 组件原读取 |
|----------------------|----------------|
| `prjUrl` | `githubPages` ❌ → 修复后：`prjUrl` ✅ |
| `prjUrl` | `url` ❌ → 修复后：`gitRepo` (fallback) ✅ |

**修复后的代码**（ProjectCard.jsx）：
```jsx
// "访问"按钮
{(project.prjUrl || project.gitRepo) && (
  <button onClick={() => window.open(project.prjUrl || project.gitRepo, '_blank')}>
    访问
  </button>
)}
// "仓库"按钮
{project.gitRepo && (
  <button onClick={() => window.open(project.gitRepo, '_blank')}>
    仓库
  </button>
)}
```

**调试步骤**：
```bash
# 1. 检查网站源码
curl -s https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/master/src/components/ProjectCard.jsx | grep -n "prjUrl"

# 2. 验证实际 JSON（绕过 CDN）
curl -s https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/gh-pages/data/proposals.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
has = sum(1 for p in d['projects'] if p.get('prjUrl'))
print(f'Projects with prjUrl: {has}/{len(d[\"projects\"])}')"

# 3. 推送修复后，GitHub Actions 自动重建
# 若 dist/ 产物未更新，手动触发：
gh workflow run "Deploy to GitHub Pages"
```

**字段命名**：
- CSV：`prj_url`（从 git_repo 推断 GitHub Pages URL）
- JSON：`prjUrl`
- ProjectCard：`prjUrl`（primary）、`gitRepo`（fallback）

## 验证检查

同步后用以下命令验证数据质量：

```bash
# 检查垃圾 p-* 项目数量
cat data/proposals.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
garbage = [p for p in data['projects'] if p['id'].startswith('p-')]
print('Garbage projects:', len(garbage))
print('Total projects:', len(data['projects']))
"

# 检查 url/gitRepo 非空率
cat data/proposals.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
has_url = sum(1 for p in data['projects'] if p.get('url'))
has_git = sum(1 for p in data['projects'] if p.get('gitRepo'))
print(f'Has url: {has_url}/{len(data[\"projects\"])}')
print(f'Has gitRepo: {has_git}/{len(data[\"projects\"])}')
"
```
