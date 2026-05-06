---
name: prj-proposals-manager-iteration-workflow
description: prj-proposals-manager 项目从 PRD 到交付的完整高速迭代流程，适用于 V4+ 的功能迭代
---

# prj-proposals-manager 高速迭代工作流

## 适用场景
prj-proposals-manager 项目从 PRD 到交付的完整迭代流程。适用于 V4+ 的功能迭代（看板增强、数据校验、导入导出、Dashboard、筛选等）。

## 核心流程（每版本约 15-20 分钟）

### Step 1: PRD 起草
- 路径: `~/.hermes/proposals/workspace-pm/proposals/P-YYYYMMDD-VX-001-prd.md`
- 内容: 功能范围 + 技术方案摘要 + 交付目标 + 优先级矩阵

### Step 2: Tech Solution 起草
- 路径: `~/.hermes/proposals/workspace-dev/proposals/prj-proposals-manager/P-YYYYMMDD-VX-001-tech-solution.md`
- 内容: 具体文件变更 + 代码实现细节 + 实现顺序

### Step 3: 提案登记（插入到正确位置）
- 路径: `~/.hermes/proposals/proposal-index.md`
- **重要**: 新条目必须添加到版本号最大的已有条目之前（即越新越靠前）
- 状态: `approved_for_dev`
- 使用足够长的 old_string（至少 3 行唯一上下文）避免打散已有条目

### Step 4: 委托 dev agent
- 传递: tech solution 路径 + 项目路径 + 构建要求
- dev agent 完成后报告: build 结果 + commit hash

### Step 5: 构建验证
```bash
cd /home/hermes/workspace-dev/proposals/prj-proposals-manager && npm run build
```

### Step 6: 验收 + PR 创建（关键！）
**重要**: dev agent 每次都会停在"未提交"状态（exit_reason: "completed"，不是 max_iterations）。这是固定模式，必须执行此步骤。

验收流程已更新为 PR 模式，详见 `dev-delivery-acceptance-checklist`：
1. 验收检查（git status / build / deployment）
2. 创建 feature branch + commit
3. 创建 PR 并提供链接给 boss
4. 5分钟超时自动合入或 boss 审批后合入
5. 合入后更新提案状态为 `delivered`

```bash
# 1. 检查未提交状态
git status

# 2. 构建验证
npm run build

# 3. 创建验收分支
git checkout -b acceptance/P-YYYYMMDD-XXX
git add <changed-files>
git commit -m "feat: V{X} {功能名}"

# 4. 推送分支
git push origin acceptance/P-YYYYMMDD-XXX

# 5. 创建 PR
gh pr create \
  --title "[Acceptance] P-YYYYMMDD-XXX: {功能名}" \
  --body "## Acceptance Checklist
- [ ] Git status: all committed
- [ ] Build: \`npm run build\` passes
- [ ] Deployment: URL accessible

## Deliverable
- Commit: \`$(git rev-parse --short HEAD)\`
- Proposal: P-YYYYMMDD-XXX" \
  --base master

# 6. 报告给 boss，等待确认或5分钟超时后自动合入
# 超时自动合入:
gh pr merge --squash --delete-branch <pr-number>
```

### Step 7: 更新提案登记
- 状态: `delivered` + `acceptance: accepted`
- Notes 末尾追加: "构建成功，GitHub Actions部署"

## 常见问题

### proposal-index.md 被打散
**原因**: 在已有条目之间插入新条目时，old_string 太短导致 patch 匹配到多个位置。

**正确做法**:
1. 新条目添加到文件末尾（版本号最大的条目之后）
2. 或确保 old_string 包含至少 3 行唯一上下文

**修复**: 发现打散后，立即 patch 用正确格式重新连接。

### gh api 大文件更新失败（argument list too long）
当 `proposals.json` 很大时，直接用 `gh api -f content=@file.json` 会因参数列表超长失败。

**正确做法**: 用 Python urllib 直接 PUT：
```python
import urllib.request, json, base64, yaml

with open('~/.config/gh/hosts.yml') as f:
    token = yaml.safe_load(f)['github.com']['oauth_token']

with open('proposals.json') as f:
    content = base64.b64encode(f.read().encode()).decode()

data = json.dumps({'message': 'chore: sync proposals', 'content': content, 'sha': sha}).encode()
req = urllib.request.Request(f'https://api.github.com/repos/{owner}/{repo}/contents/{path}', data=data, headers={'Authorization': f'token {token}', 'Content-Type': 'application/json'}, method='PUT')
urllib.request.urlopen(req)
```

### dev agent 停在"未提交"状态（V11-V15 实测：100%发生）
**现象**: dev agent 报告 "completed" 但 git status 显示 "Changes not staged for commit"。
**原因**: dev agent 完成任务后未执行 git commit。这是固定行为，不是边缘 case。
**处理**: 每次都必须手动检查 git status → npm run build → git add/commit/push。

**例外（V26/V27 实测）**: dev agent 有时会在同一 commit 中合并多个功能。
- **特征**: git status 只显示 "M dist/index.html"，无 untracked 文件
- **验证方法**: 检查 `git log --oneline -3`，确认最新 commit 是否已包含功能代码
- **验证工具**: `grep -r "功能关键词" src/` 搜索实际文件
- **结论**: 如果最新 commit 已包含代码，说明 dev agent 已经在上一个版本提交中完成了本次工作

### Git push 冲突（V20 实测）
**现象**: `git push` 报错 `failed to push because the remote contains work that you do not have`。

**原因**: 远程有新的 commit（通常是 GitHub Actions 自动部署触发的 commit），本地落后。

**修复**:
```bash
git stash                    # 暂存本地变更
git pull --rebase origin master  # 拉取并变基
git stash pop                # 恢复本地变更
git push origin master       # 推送
```

### feature 分支与其他迭代的 UI 重构冲突
**现象**: 已有 feature 分支（如 feature/v4-swimlanes-search-batch），其他迭代对通用组件做了重大重构（如 Header 精简）后，merge/rebase 产生大量冲突。

**原因**: feature 分支基于旧代码，分支后对共享组件的修改导致冲突。

**正确做法**:
```bash
# 放弃旧分支，从 master 新建
git checkout master
git branch -D feature/xxx-search-batch  # 删除旧分支
git checkout -b feature/xxx             # 从 master 新建分支
# 重新委托 dev agent
```

**教训**: 当 feature 分支依赖的组件被重构时，merge 成本高于重建。本场景中 Header 组件精简导致 12 个文件冲突。识别特征：`git diff master...HEAD --stat` 显示大量公共组件变更。

### subagent 重复函数
subagent 交付后可能出现重复函数定义。需检查 git diff，手动删除重复项后重新 commit。

### App.jsx 读取字段与数据不匹配（githubPages vs url）
**现象**: "访问"按钮不显示，但 `data/proposals.json` 中已有 `githubPages` 字段。
**原因**: 前端 `App.jsx` 中按钮条件判断用的是 `project.url`，但数据字段是 `githubPages`。
**修复**: 
1. 克隆到 `/tmp/` 调试：`git clone --depth=1 https://github.com/YeLuo45/prj-proposals-manager.git /tmp/prj_pm_test`
2. 在 `flatMap` 回调中添加 `projectGitPages: project.githubPages,`
3. 将 `{project.url && (` 改为 `{(project.githubPages || project.url) && (`
4. 将 `window.open(project.url` 改为 `window.open(project.githubPages || project.url`
5. 用 `patch` 工具修改，避免字符串替换产生重复 fragment
6. 构建验证：`cd /tmp/prj_pm_test && npm run build`
7. 提交推送：`git add src/App.jsx && git commit -m "fix: ..." && git push origin master`

### 'as const' TypeScript 语法错误导致构建失败（V22 实测）
**现象**: `npm run build` 报错 `Expected "}" but found "as"`，且 esbuild 指向 JSX 文件（如 ProposalCard.jsx、SwimlaneCard.jsx）。
**原因**: dev agent 在 style 对象中使用了 TypeScript `as const` 断言（如 `position: 'absolute' as const`），但项目使用 .jsx 而非 .tsx，且 esbuild 不支持此语法。
**特征**: 错误行类似 `position: 'absolute' as const,` — 多出现在返回 style 对象的函数中。
**修复**: 移除 `as const` 后缀。
```bash
# 批量查找所有 'as const' 用法
grep -r "as const" src/

# 修复（以 ProposalCard.jsx 为例）
sed -i "s/position: 'absolute' as const/position: 'absolute'/g" src/components/ProposalCard.jsx
sed -i "s/position: 'absolute' as const/position: 'absolute'/g" src/components/SwimlaneCard.jsx
npm run build
```

### JSX/TSX 标签不匹配导致构建失败（V22 实测）
**现象**: esbuild 报错 `This JSX tag type has no corresponding JSX tag provider` 或 tag mismatch。
**原因**: dev agent 在 JSX 中混用了不匹配的开闭标签，或在 .jsx 文件中使用了 TypeScript-only 语法。
**修复**: 检查报错文件，通常需要补充缺失的闭合标签或修复 TypeScript 语法。运行 `grep -n "<" src/pages/XXX.jsx | head -50` 排查。
**现象**: `npm run build` 报错 `Rollup failed to resolve import "jspdf"`，且 `node_modules/jspdf/dist/` 只有 polyfills 文件，缺少主 JS 文件。
**原因**: 某些 jspdf 版本安装不完整，或 dev agent 使用了错误的 import 路径。
**正确 import**:
```javascript
import jsPDF from 'jspdf';  // 正确
```
**错误 import**:
```javascript
import { jsPDF } from 'jspdf/dist/jspdf.es.min.js';  // 错误
```
**修复步骤**:
```bash
npm uninstall jspdf
npm install jspdf@2.5.1
# 验证安装
ls node_modules/jspdf/dist/*.js  # 应有 jspdf.es.js 等文件
npm run build
```

## 技术栈
- React 18 + Vite 5 + Tailwind + Chart.js + react-chartjs-2
- GitHub Pages 部署（GitHub Actions auto-deploy on master push）
- localStorage 持久化（筛选模板、历史记录、折叠状态等）
- PWA + Service Worker（v15，当前缓存名 proposals-manager-v15）
- 部署路径: `/prj-proposals-manager/`（子目录）

## 构建系统关键行为（经验总结）

### dist 目录完全重写
`npm run build` 会**完全重建** `dist/` 目录，所有非构建生成的文件都会被覆盖。
- **教训**: 修改 `dist/` 中的文件（如 manifest.json、sw.js）后，如果再次运行 build，这些修改会丢失
- **正确做法**: 修改 `public/` 目录下的源文件，构建后检查 `dist/` 是否正确

### PWA / Service Worker 维护注意事项
1. **生成 PNG 图标**: 用 PIL 生成有效图标，放在 `public/icons/`（不是 `dist/icons/`），构建时会自动复制
2. **manifest.json 路径**: `public/manifest.json` 中 `icons[*].src` 用 `./icons/...`（相对路径），`start_url` 用 `/prj-proposals-manager/`（子目录部署）
3. **sw.js 路径**: `public/sw.js` 中所有路径都用相对路径 `./`
4. **build 后重新生成图标**: 构建会覆盖 `public/icons/` 的 PNG（只保留 SVG），需构建后重新生成

### GitHub Pages 子目录部署路径规则
网站部署在 `https://yeluo45.github.io/prj-proposals-manager/`（不是根路径）。
- HTML 中的资源链接用 `./manifest.json`（相对路径）
- manifest 中 `start_url` 必须是 `/prj-proposals-manager/`
- SW 中缓存的资源路径用 `./data/...` `./icons/...`
- **绝对路径 `/data/...` 在 SW 中会解析为 `https://yeluo45.github.io/data/...` 而非子目录路径**

### SW 缓存策略
- 使用 `cache.add(asset)` 逐个缓存，避免 `cache.addAll([...])` 中一个 404 导致整个缓存失败
- SW 版本号每次修改递增（当前 v15）
- 旧版本 SW 的缓存通过 `activate` 事件清理

## 相关文件
- 源码: `/home/hermes/workspace-dev/proposals/prj-proposals-manager/`（或 `/tmp/prj-proposals-manager/`）
- 提案: `~/.hermes/proposals/workspace-pm/proposals/`
- 索引: `~/.hermes/proposals/proposal-index.md`
