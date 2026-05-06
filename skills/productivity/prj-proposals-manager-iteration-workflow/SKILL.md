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

### Step 6: Git commit + push（关键！）
**重要**: dev agent 每次都会停在"未提交"状态（exit_reason: "completed"，不是 max_iterations）。这是固定模式，必须执行此步骤。

```bash
# 1. 检查未提交状态
git status

# 2. 构建验证
npm run build

# 3. 提交（选择关键文件，避免 dist/ 意外变更）
git add src/... package.json package-lock.json  # 按实际变更的文件
git commit -m "feat: V{X} {功能名}"

# 4. push
git push origin master
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

### subagent 重复函数
subagent 交付后可能出现重复函数定义。需检查 git diff，手动删除重复项后重新 commit。

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

## 相关文件
- 源码: `/home/hermes/workspace-dev/proposals/prj-proposals-manager/`
- 提案: `~/.hermes/proposals/workspace-pm/proposals/`
- 索引: `~/.hermes/proposals/proposal-index.md`
