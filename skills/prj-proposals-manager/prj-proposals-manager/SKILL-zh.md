---
name: prj-proposals-manager
description: 管理从需求 intake 到交付的完整提案生命周期，协调多个 Agent 或角色（Coordinator / PM / Dev / Test Expert / Research Analyst）。涵盖 intake、澄清、PRD 确认、技术评审、测试用例生成、开发交接、验收和交付。支持任意 Agent 平台（Cursor、Hermes、OpenClaw 等）
version: 2.5.0
author: YeLuo45
license: MIT
metadata:
  hermes:
    tags: [proposal, workflow, lifecycle, project-management, coordinator, pm, dev, test, research]
    homepage: https://yeluo45.github.io/prj-proposals-manager/
    related_skills: [harness-desktop-iteration-workflow, dbg-card-game-workflow, pixel-pal-web-workflow]
---

# 提案管理

一个与平台无关的技能，用于在多角色工作流（Coordinator / PM / Dev / Test Expert / Research Analyst）中管理提案生命周期。涵盖 intake、澄清、PRD 确认、技术评审、测试用例生成、开发交接、验收和交付。

## 架构：CSV 作为真相来源

```
+------------------+       +---------------------+       +------------------+
||   CSV Files      | <--> |  proposal_manager   | -->   |  Markdown Files  ||
|| (source of truth)|       |  _cli.py            |       | (derived)        |
+------------------+       +---------------------+       +------------------+
        |                                                       |
        v                                                       v
+------------------+                                   +------------------+
||  Local CSVs      |                                   |  GitHub JSON     |
||  (not on GitHub) | <------- pull-proposals -------- |  (proposals.json)|
+------------------+       (GitHub is JSON format)    +------------------+
                                    ^
                                    |
                          +------------------+
                          |  sync-proposals  |
                          |  -to-website.py  |
                          +------------------+
                          (CSV -> JSON push)
```

**数据流：**
1. 所有变更通过 `proposal_manager_cli.py` 进行（写入 CSV）
2. CSV 文件是**唯一的真相来源**
3. `sync-proposals-to-website.py` 读取 CSV 并推送到 GitHub（推送到 `gh-pages` 分支）
4. LLM 根据 CSV 内容生成/更新 markdown 文件（`proposal-index.md`、`proposal-docs-index.md`、`project-index.md`）

## 关键：GitHub Pages 从 gh-pages 分支提供服务

**网站 `https://yeluo45.github.io/prj-proposals-manager/` 从 `gh-pages` 分支读取内容，而非 `master`。**

- `sync-proposals-to-website.py` 默认推送到 `gh-pages` 分支
- `master` 分支可能包含不同内容（用于开发/源码）
- 同步完成后，始终通过 `curl https://yeluo45.github.io/prj-proposals-manager/data/proposals.json` 或 `curl https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/gh-pages/data/proposals.json` 验证
- 原始 GitHub API（`api.github.com`）默认使用 `master` 分支——使用 `?ref=gh-pages` 来指定部署分支

## 快速开始

```bash
# 初始化（首次使用）
python3 scripts/init_proposals_dir.py

# 创建项目（带本地工作空间初始化）
python3 scripts/proposal_manager_cli.py project add --name "ProjectName" --git-repo "https://github.com/owner/repo" --init-workspace

# 创建提案（本地项目路径自动确定）
python3 scripts/proposal_manager_cli.py proposal add --title "ProposalTitle" --project-id PRJ-YYYYMMDD-XXX

# 更新提案字段
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status in_dev
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --deployment-url "https://..."

# 更新项目字段
python3 scripts/proposal_manager_cli.py project update PRJ-YYYYMMDD-XXX --name "NewName"

# 查看状态
python3 scripts/proposal_manager_cli.py proposal list --fields id,title,status,project_name
python3 scripts/proposal_manager_cli.py project list --fields id,name,proposal_count

# 同步到网站（CSV -> GitHub）
GITHUB_TOKEN=$GITHUB_TOKEN python3 scripts/sync-proposals-to-website.py

# 备份
bash scripts/backup_proposals.sh
```

## 操作模式

### 默认模式（交互式）

需要用户确认时，提供 A/B/C/D 选项并等待单字母回复：
- 选项以括号形式呈现：`[A] 选项 A  [B] 选项 B  [C] 选项 C  [D] 继续`
- 用户以单个字母回复（不区分大小写）
- 超时后触发第一个选项作为默认

### 无人值守模式（全自动）

适用于无用户在场时的持续迭代。当请求者/boss 在提交提案时指定"无人值守"或"自动"时启用。

**如何进入：**
- Boss/请求者声明意图："我要无人值守模式跑这个项目"或"run in unattended mode"
- 在提案的 `notes` 字段中记录为 `mode: unattended`
- 一旦进入，所有后续迭代自动保持无人值守模式

**特性：**
- 始终自动选择第一个选项（默认）
- 不等待用户输入
- 交付时必定包含迭代方向选项（A/B/C/D），确保迭代持续
- 永远不会在确认门控上卡住
- 无人值守模式跨迭代保持——一旦设置，持续有效直到 boss 明确退出

**传递规则：**
- 当在无人值守模式项目下创建新迭代提案时，继承无人值守模式
- 交付后不清除无人值守模式——持续迭代直到 boss 明确退出

**触发时机：**
- 交付时：始终提供 A/B/C/D 迭代选项，5分钟超时后自动选择第一个
- PRD/技术预期确认：5分钟超时后自动批准并继续
- 无人值守模式下不提问澄清问题

**用法：**
```bash
# Boss 在提案时声明
"我要无人值守模式跑这个项目" 或 "run in unattended mode"

# 在提案 notes 字段中记录：
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --notes "mode: unattended"
```

## CSV 结构（真相来源）

### projects.csv

```
id,name,proposal_count,git_repo,local_path,prj_url,description,last_update
PRJ-20260419-007,ai-creator-h5,3,https://github.com/owner/repo,/path/to/local,https://owner.github.io/ai-creator-h5,My project,2026-05-15
```

- `prj_url`：部署 URL——GitHub Pages、Cloudflare Pages、Netlify 或其他托管平台。格式各异：GitHub Pages 为 `https://yeluo45.github.io/{repo}/`，Cloudflare/Netlify 为直连域名。仅对 YeLuo45/* 仓库设置。

### proposals.csv
proposals.csv — 20-Field Structure (STRICT)
```
id,title,owner,status,project_id,project_name,stage,prd_path,tech_solution_path,project_path,deployment_branch,prd_confirmation,tech_expectations,acceptance,research_direction,last_update,engine,target,game_type,notes
P-20260505-001,PRD: Monopoly3D 核心体验打磨,,active,PRJ-20260412-009,Monopoly3D,intake,workspace-pm/proposals/PRJ-20260412-009/P-20260505-001-prd.md,,/home/hermes/workspace-dev/proposals/monopoly3d,gh-pages,,,,,,2026-05-05,,,,
```

### project_proposal_mapping.csv

```
project_id,project_name,proposal_id,proposal_name
```

## 工作流：提案生命周期

```
Step 1a/1b: Intake -- 注册提案（从现有代码库或新建）
Step 2: Clarify -- 最多3轮澄清
Step 3: 如需要则转给 PM
Step 4: PRD 确认门控
Step 5: 技术预期门控（最多3轮）
Step 6: 输出技术方案
Step 6b: 交接给 Test Expert -- 生成 TDD 测试用例
Step 7: 交接给 Dev（以测试用例为参考）
Step 8: Test Expert 基于测试用例进行验收
Step 9: 交付或返修
Step 10: 研究方向（验收后迭代规划）
Step 11: 部署（验收后交付）
Step 12: 网站重建
```

### Step 1a: 从现有代码库注册

当需求是克隆现有 GitHub 仓库并注册为提案时（而非从零开始构建）：

1. 将仓库克隆到 `$DEV_OUTPUT_DIR/<project-name>/proposals/` 或本地复制

2. 对于设计文档项目（`*-design`），按照 Step 1b 作为常规提案处理

### Step 1b: 从零开始注册新提案

1. 使用 `proposal_manager_cli.py` 确定下一个 PRJ_ID 和 P-ID：
   ```bash
   # 生成下一个项目 ID
   python3 scripts/proposal_manager_cli.py project next-id

   # 为项目生成下一个提案 ID
   python3 scripts/proposal_manager_cli.py proposal next-id PRJ-YYYYMMDD-XXX
   ```
2. 为此提案创建 feature 分支（如果项目有远程仓库）：
   ```bash
   cd $DEV_PROPOSALS/<project-name>
   git checkout -b feature/P-YYYYMMDD-XXX
   ```
3. 将 `$TEMPLATES_DIR/request-intake-template.md` 复制到 `$PM_PROPOSALS/PRJ-YYYYMMDD-XXX/P-YYYYMMDD-XXX.md`
4. 填写基本信息和原始需求
5. 在 `$PROJECTS_CSV`（projects.csv）中添加项目条目
6. 在 `$PROPOSAL_DOCS_INDEX` 中为此提案添加条目
7. 创建项目目录结构：
   ```bash
   mkdir -p $DEV_PROPOSALS/<project-name>/docs
   mkdir -p $PM_PROPOSALS/PRJ-YYYYMMDD-XXX
   ```

### Step 2: 澄清需求

- 最多向请求者进行3轮澄清提问，聚焦于：目标、范围、约束、验收标准
- 在提案文件的"Clarification"部分记录每轮问答
- 3轮之后或需求清晰时，记录最终假设
- 将状态更新为 `clarifying`：
  ```bash
  python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status clarifying
  ```

### Step 3: 转给 PM

如果需求只是一个想法或粗略草案，转给 PM 角色来生成 PRD。

- PM 将 PRD 保存到 `$PM_PROPOSALS/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md`
- PM 还将 PRD 复制到 `$DEV_PROPOSALS/<project-name>/docs/prd.v1.md`
- 在 proposals.csv 中更新 PRD 路径：
  ```bash
  python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --prd-path "$PM_PROPOSALS/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md"
  ```

### Step 4: PRD 确认门控

PM 返回 PRD 后：

1. 向请求者展示 PRD 并请求确认
2. 开始确认倒计时（建议：5分钟）
3. 在"PRD Confirmation Countdown ID"中记录倒计时引用

如果确认：将 PRD Confirmation 设为 `confirmed`，取消倒计时，立即将状态更新为 `approved_for_dev` 并开始开发。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --prd-confirmation confirmed --status approved_for_dev
```

如果超时：将 PRD Confirmation 设为 `timeout-approved`，在"Timeout Resolution"中记录，立即将状态更新为 `approved_for_dev` 并开始开发。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --prd-confirmation timeout-approved --status approved_for_dev
```

### Step 5: 技术预期门控

在输出技术方案之前：

1. 从请求者处了解：技术栈、性能、成本、部署方式、可维护性、依赖约束
2. 最多3轮提问
3. 开始确认倒计时（与 Step 4 相同机制）
4. 在"Technical Expectations Countdown ID"中记录

如果确认：将 Technical Expectations 设为 `confirmed`，立即撰写技术方案并将状态更新为 `approved_for_dev`。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --tech-expectations confirmed --status approved_for_dev
```

如果超时：将 Technical Expectations 设为 `timeout-approved`，按当前假设继续，立即撰写技术方案并将状态更新为 `approved_for_dev`。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --tech-expectations timeout-approved --status approved_for_dev
```

### Step 6: 技术方案

- 将技术方案输出到 `$PROPOSALS_ROOT/P-YYYYMMDD-XXX-tech-solution.md`
- 同时复制到 `$DEV_PROPOSALS/<project-name>/docs/technical-solution.v1.md`
- 更新 tech_solution_path 和状态：
  ```bash
  python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --tech-solution-path "$PROPOSALS_ROOT/P-YYYYMMDD-XXX-tech-solution.md" --status approved_for_dev
  ```

### Step 6b: TDD 测试用例生成

技术方案输出后，转交给 Test Expert 基于 TDD 原则生成测试用例：

1. Coordinator 将任务交接给 Test Expert，包含：PRD 文档、技术方案文档、项目背景

2. Test Expert 将测试用例输出到 `$TEST_OUTPUT_DIR/<project-name>/YYYY-MM-DD-test-cases.md`
   - 测试用例必须可追溯到 PRD 需求
   - 包含：测试用例 ID、描述、前置条件、步骤、预期结果
   - 覆盖正常路径和边界情况
   - 将测试用例复制到 `$DEV_OUTPUT_DIR/<project-name>/proposals/docs/test-cases.v1.md`

3. 更新追踪：更新 Test Cases 路径和状态：
  ```bash
  python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --test-cases-path "$TEST_PROPOSALS/<project-name>/YYYY-MM-DD-test-cases.md" --status in_tdd_test
  ```

### Step 7: 交接给开发

- 将状态更新为 `in_dev`：
  ```bash
  python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status in_dev
  ```
- 更新 project_path：
  ```bash
  python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --project-path "$DEV_PROPOSALS/<project-name>"
  ```
- 如果目录不存在，Dev 创建 `$DEV_PROPOSALS/<project-name>/docs/`

### Step 8: Test Expert 验收（基于 TDD）

Dev 报告完成后，Test Expert 基于测试用例执行验收：

需求一致性：
- 符合请求者确认的需求
- 与 PRD 对齐
- 无范围蔓延或偷工减料

测试用例执行：
- 执行 `test-cases.vN.md` 中的每个测试用例
- 记录每个测试用例的通过/失败状态
- 记录任何偏差或失败

功能验证（必须实际操作，不能只看截图）：
- 核心功能端到端正常工作
- 控制台/日志无 Error（warning 可以忽略）
- 现有功能未被破坏
- 构建成功

验收期间将状态更新为 `in_test_acceptance`。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status in_test_acceptance
```

如果所有测试用例通过：进入 Step 9（交付）

如果任何测试用例失败：将状态更新为 `test_failed`，输出结构化返修意见。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status test_failed
```

### Step 9: 交付或返修

如果所有测试用例通过：将状态更新为 `accepted`，进入 Step 10（研究方向）。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status accepted
```

如果验收失败：将状态更新为 `needs_revision`，输出结构化返修意见。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status needs_revision
```

### Step 10: 研究方向（验收后迭代规划）

验收通过后（状态变为 `accepted` 或 `delivered`）：

1. Coordinator 询问请求者："基于本次交付，你是想探索下一个迭代方向，还是先维护当前版本？"
2. 开始5分钟确认倒计时，创建 cron job
3. 在"Research Direction Countdown ID"中记录倒计时引用

如果确认：将 Research Direction 设为 `confirmed`，立即将任务转给 PM 生成下一个迭代 PRD。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --research-direction confirmed
```

如果超时：将 Research Direction 设为 `timeout-approved`，Coordinator 自行决定，立即将任务转给 PM 生成下一个迭代 PRD。
```bash
python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --research-direction timeout-approved
```

### Step 11: 部署（验收后交付）

验收通过后（状态变为 `accepted`）：

1. 确定部署目标：GitHub Pages 或 Cloudflare Pages
2. 创建部署分支
3. 准备部署（确保 package-lock.json 已提交，运行 `npm run build`）
4. 推送到远程
5. 推送至远程
6. 触发部署
7. 更新提案：将状态设为 `deployed`，记录 Deployment URL 和 Deployment Branch：
   ```bash
   python3 scripts/proposal_manager_cli.py proposal update P-YYYYMMDD-XXX --status deployed --deployment-url "https://..." --deployment-branch gh-pages
   ```
8. 同步到 proposals-manager 网站 + hermes-agent

### Step 12: 网站重建

- 使用 `proposal-sync-website` skill 更新 YeLuo45/prj-proposals-manager 中的 `data/proposals.json`
- 同步后重建网站：从 GitHub API 下载更新的 `proposals.json` 到 `public/data/proposals.json`，然后 `npm run build` 并部署到 gh-pages

## 开发交付质量检查

验收前必须验证三项硬指标：

1. 构建 exit code：必须为 0
2. 输出目录非空：列出核心文件确认
3. 核心源文件/服务文件存在：验证关键文件存在

### 接管触发条件

满足任一条件时 Coordinator 应直接接管：
- Dev 连续2次交付不合格
- Dev session 因 API/配额错误中断
- Dev session 异常短（<30秒）却声称完成
- 修复方法简单明确

### 修复记录

当 Coordinator 直接修复问题时，记录到：
1. 项目 memory 文件（例如 `MEMORY.md`）的相关章节
2. 每日日志（例如 `memory/YYYY-MM-DD.md`）
3. 提案的 Notes 或 Main Fixes Applied 字段

## 索引条目模板

添加到 `proposal-index.md` 时：

### P-YYYYMMDD-XXX: <Title>

- Proposal ID: P-YYYYMMDD-XXX
- Title: <Title>
- Owner: <Coordinator>
- Current Status: <Status>
- PRD Path: (由 PM 填写)
- Technical Solution: (待填写)
- Test Cases Path: (由 Test Expert 填写)
- Project Path: (由 Dev 填写)
- Acceptance: -
- PRD Confirmation: pending
- PRD Confirmation Countdown ID: -
- Technical Expectations: pending
- Technical Expectations Countdown ID: -
- Research Direction: pending
- Research Direction Countdown ID: -
- Deployment URL: (部署后填写)
- Deployment Branch: (部署后填写)
- Last Update: YYYY-MM-DD
- Notes:

## 脚本

| Script | Purpose |
|--------|---------|
| init_proposals_dir.py | 初始化/修复提案目录结构 |
| proposal_manager_cli.py | projects 和 proposals 的 CRUD（所有 CSV 操作都通过此脚本） |
| edit_proposal.py | 旧版 markdown+CSV 字段编辑器（新工作请使用 cli.py） |
| sync-proposals-to-website.py | 读取 CSV，推送到 GitHub，生成网站 JSON |
| pull-proposals-from-github.py | 从 GitHub 拉取 proposals.json 并转换为本地 CSV |
| backup_proposals.sh | 备份所有提案系统数据 |
| rollback_proposals.sh | 回滚：全系统、按项目或按提案从备份恢复 |
| sync-pm-to-dev.py | 验收后将 PRD/技术方案/测试用例从 workspace-pm 同步到 workspace-dev |
| generate-spec.py | 验收后基于提案生成 OpenSpec SPEC 文件到 workspace-dev/proposals/{project}/SPEC |

## 备份和回滚

### 备份

```bash
# 创建备份（保留最近10个备份）
bash scripts/backup_proposals.sh

# 备份存储在：/home/hermes/proposals/backups/
```

### 回滚

```bash
# 列出可用备份
bash scripts/rollback_proposals.sh list

# 验证备份完整性
bash scripts/rollback_proposals.sh verify proposals_backup_YYYYMMDD_HHMMSS.tar.gz

# 全系统回滚（到最新备份）
bash scripts/rollback_proposals.sh full

# 全系统回滚到指定备份（N=1 为最新，N=2 为第二新）
bash scripts/rollback_proposals.sh full 3

# 回滚指定项目
bash scripts/rollback_proposals.sh project PRJ-YYYYMMDD-XXX

# 回滚指定提案
bash scripts/rollback_proposals.sh proposal P-YYYYMMDD-XXX
```

### 回滚行为

| Command | Data Restored |
|---------|---------------|
| `full N` | 备份 N 中的所有 CSV + markdown 文件 |
| `project <id> N` | projects.csv 条目 + 相关提案 + 映射 |
| `proposal <id> N` | proposals.csv 中的单个提案 + 映射 |

**安全措施：**
- 全系统回滚前：创建当前状态的紧急备份
- 提案/项目回滚前：创建紧急备份
- 所有操作需要 `yes` 确认

## 配置

| Variable | Value | Description |
|----------|-------|-------------|
| PROPOSALS_ROOT | `/home/hermes/proposals` | 存放 CSV 和 markdown 文件的目录 |
| DEV_OUTPUT_DIR | `/home/hermes/proposals/workspace-dev/<project>/proposals` | Dev 工作空间 |
| PM_OUTPUT_DIR | `/home/hermes/proposals/workspace-pm/<project>/proposals` | PM 工作空间 |
| TEST_OUTPUT_DIR | `/home/hermes/proposals/workspace-test/<project>/proposals` | Test 工作空间 |
| RESEARCH_OUTPUT_DIR | `/home/hermes/proposals/workspace-research/<project>/proposals` | Research 工作空间 |

## 数据规则

1. **CSV 是真相来源** - 所有变更必须通过 `proposal_manager_cli.py`
2. **Markdown 文件是派生文件** - 由 LLM 根据 CSV 内容生成/更新
3. **GitHub 远程是 JSON，不是 CSV** - 远程 `data/` 包含 `proposals.json`、`todos.json`、`milestones.json`。CSV 文件不在 GitHub 上，也从未成功推送过。
4. **从 GitHub 恢复** - 使用 `pull-proposals-from-github.py` 从 `proposals.json`（GitHub 的规范格式）拉取并转换为本地 CSV。对于历史恢复，查看 GitHub 提交历史（例如 `?path=data/proposals.json&since=YYYY-MM-DD`）以查找特定版本。
5. **CSV 重复列预防** - 读取 CSV 并重写时（例如在同步脚本中），始终明确去重列。重复的 `prj_url` 列会破坏 CSV。参见 `references/data-model.md#duplicate-columns`。

## 提案状态

在所有角色中使用这些确切名称：

```
intake -> clarifying -> prd_pending_confirmation -> approved_for_dev -> in_tdd_test -> in_dev -> in_test_acceptance -> accepted -> deploying -> deployed
                                                                                   |                              |
                                                                         needs_revision -> in_dev              test_failed -> in_dev
```

## 工作空间初始化

使用 `--init-workspace` 创建项目时，脚本会创建：

```
workspace-dev/<project>/proposals/
workspace-dev/<project>/proposals/docs/index.md

workspace-pm/<project>/proposals/
workspace-pm/<project>/proposals/docs/index.md

workspace-test/<project>/proposals/
workspace-test/<project>/proposals/docs/index.md

workspace-research/<project>/proposals/
workspace-research/<project>/proposals/docs/index.md
```

每个 `docs/index.md` 包含 Proposal、PRD、Technical Solution 和 Test Cases 的版本追踪表。

## 通过 CLI 编辑字段

所有 CSV 字段都可以通过 `proposal_manager_cli.py` 更新：

```bash
# 更新提案字段
python3 scripts/proposal_manager_cli.py proposal update <id> \
    --status in_dev \
    --title "PRD: Feature Name" \
    --owner boss \
    --project-id PRJ-20260516-001 \
    --stage intake \
    --prd-path "workspace-pm/proposals/PRJ-20260516-001/my-proposal-prd.md" \
    --tech-solution-path "workspace-pm/proposals/PRJ-20260516-001/my-proposal-tech.md" \
    --project-path "/home/hermes/workspace-dev/proposals/my-project" \
    --deployment-url "https://yeluo45.github.io/my-project/" \
    --deployment-branch gh-pages \
    --prd-confirmation confirmed \
    --tech-expectations confirmed \
    --acceptance passed \
    --research-direction "Expand to mobile" \
    --engine Unity \
    --target "iOS,Android" \
    --game-type RPG \
    --notes "Fixed critical bug"

# 更新项目字段
python3 scripts/proposal_manager_cli.py project update <id> \
    --name "New Name" \
    --git-repo "https://github.com/YeLuo45/new-repo" \
    --local-path "/home/hermes/workspace-dev/proposals/new-repo" \
    --description "Project description"
```

### 验收后：将 PRD/技术方案同步到 Dev 工作空间

提案验收后，需将 PRD 和技术方案文件同步到 `workspace-dev/proposals/` 下对应的项目目录，确保项目同步到远程仓库时包含这些文档：

```bash
python3 scripts/sync-pm-to-dev.py <project_id> [--dry-run]

# 示例
python3 scripts/sync-pm-to-dev.py PRJ-20260422-001          # 同步 ai-novel-assistant
python3 scripts/sync-pm-to-dev.py PRJ-20260516-001 --dry-run  # 仅预览
```

文件从：`workspace-pm/proposals/{project_id}/` → `workspace-dev/proposals/{project_name}/`

测试用例文件（文件名包含 `test`、`spec`、`test-case` 的 .md 文件）也会被同步。

### 验收后：生成 OpenSpec SPEC

提案验收后，基于 PRD 和技术方案生成 OpenSpec 规范文件：

```bash
python3 scripts/generate-spec.py <project_id> [--dry-run]

# 示例
python3 scripts/generate-spec.py PRJ-20260422-001          # 为 ai-novel-assistant 生成 SPEC
python3 scripts/generate-spec.py PRJ-20260516-001 --dry-run  # 仅预览
```

读取 `workspace-pm/proposals/{project_id}/` 下的 PRD 和技术方案，生成：

```
workspace-dev/proposals/{project_name}/SPEC/
├── proposal.md        # Why/What/Capabilities/Impact（来自 PRD）
├── spec.md           # 需求 + GHERKIN 场景
├── design.md         # Context/Goals/Decisions/Risks（来自技术方案）
├── tasks.md          # 实施检查清单
└── .openspec.yaml    # 元数据（schema、project、创建日期）
```

OpenSpec 参考：https://github.com/YeLuo45/OpenSpec（schemas/spec-driven/templates/）

### 为已有项目初始化 SPEC

为没有提案的项目（遗留项目）从现有项目文件初始化 OpenSpec SPEC：

```bash
# 为单个项目初始化 SPEC（按项目名）
python3 scripts/generate-spec.py --init <project_name>
python3 scripts/generate-spec.py --init todolist                      # 按项目名
python3 scripts/generate-spec.py --init ai-stock-simulation --name "AlphaTrader"  # 带显示名

# 为所有没有 SPEC 的项目初始化
python3 scripts/generate-spec.py --init --all
python3 scripts/generate-spec.py --init --all --dry-run               # 仅预览
```

读取来源：
- `workspace-dev/proposals/{project_name}/README.md`（项目描述、功能、技术栈）
- `workspace-dev/proposals/{project_name}/SPEC.md`（如果存在）
- 无来源时使用模板内容

## 重要注意事项

### 路径发现

Hermes 环境：
- `/home/hermes/proposals/` 是实际的提案根目录（2026-05-21 从 `~/.hermes/proposals/` 迁移）
- 主索引文件是 `proposal-docs-index.md`（不是 `proposal-index.md`）

OpenClaw 环境（Windows/WSL）：
- 提案根目录：`~/.openclaw/workspace/proposals/`
- 主索引文件是 `proposal-index.md`
- PM 输出：`~/.openclaw/workspace-pm/proposals/`
- Dev 输出：`~/.openclaw/workspace-dev/proposals/`

### 关键：execute_code 文件写入会删除所有换行

通过 execute_code 写回 `proposal-index.md` 时，整个文件会变成一行。写入前务必备份。

安全方法：
1. 写回之前，`cp proposal-index.md proposal-index.md.bak`
2. 或先写到 `/tmp/`，验证内容后再覆盖
3. 切勿直接在 execute_code 中覆盖 `proposal-index.md`

### GITHUB_TOKEN 必须导出

运行需要 GitHub 认证的同步/拉取脚本时：
- **错误**：`GITHUB_TOKEN=$GITHUB_TOKEN python3 script.py`（子 shell 不会继承）
- **正确**：`export GITHUB_TOKEN=$(gh auth token) && python3 script.py`
- 或者：`GITHUB_TOKEN=$(gh auth token) python3 script.py`（命令替换可以内联工作）

### GitHub Actions 构建缓存陷阱

**`cache: ''` 不会禁用缓存**——它会启用 npm 自己的缓存：

```yaml
# 错误——这会启用 npm 缓存
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: ''   # 这不是空的；npm 使用自己的缓存策略
```

**正确方法——真正禁用缓存：**

```yaml
# 选项 1：显式使用 npm 缓存
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'

# 选项 2：完全删除 cache 行（完全不缓存）
- uses: actions/setup-node@v4
  with:
    node-version: '20'
```

**即使没有显式缓存，Actions 仍可能重用旧的 node_modules/build 产物。** 如果 GitHub Pages 显示过时的 JS（尽管部署成功）：

1. 检查已部署的 JS：`curl -s https://yeluo45.github.io/prj-proposals-manager/assets/index-*.js | tr ';' '\n' | grep -i "fe\.prjUrl"`
2. 如果 JS 过时（显示 `fe.githubPages||fe.url` 而不是 `fe.prjUrl||fe.githubPages||fe.url`）：
   - 验证源代码正确：`curl -s https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/master/src/components/ProjectCard.jsx | grep prjUrl`
   - Actions 构建没有重新编译——可能在重用缓存的构建产物
3. **通过 REST API 恢复**（当 `git push --force` 被阻止时）：
   - 从已知良好的 commit 下载正确文件：`curl -s https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/{good-sha}/src/components/ProjectCard.jsx -o /tmp/ProjectCard.jsx`
   - 获取当前 SHA：`curl -s -X GET -H "Authorization: Bearer *** "https://api.github.com/repos/{owner}/{repo}/contents/src/components/ProjectCard.jsx"`
   - 通过 REST API 推送：`PUT /repos/{owner}/{repo}/contents/src/components/ProjectCard.jsx`，包含 base64 编码内容和当前 SHA
   - 这样可以避免需要 `git push --force`

**切勿将编译后的 JS 推送到源文件**——如果你从 GitHub Pages 下载编译后的 `.js` 并作为 `ProjectCard.jsx` 推送，你就用编译代码破坏了源码。始终保持源文件（`.jsx`、`.tsx`）和构建产物（`dist/`）分开。

### WSL GitHub API 可靠性

WSL 到 GitHub API 的网络不可靠（超时、403、409）。有效的模式：
- 直接 `curl` 加 `--max-time 20` 往往能成功，而 `gh api` 会超时
- PUT 前始终获取当前 SHA：`curl -s --max-time 20 -X GET "https://api.github.com/repos/.../contents/...?ref=gh-pages"`
- 对于大payload（>100KB），`gh api` 比原始 `curl` 更可靠
- 如果 PUT 返回 409 Conflict，说明 SHA 已更改——重新获取 SHA 并重试
- 网络可能在 10-30秒 睡眠后恢复；脚本逻辑应处理这种情况

**同步的分支定位：**
- `sync-proposals-to-website.py` 默认推送到 `gh-pages` 分支（GitHub Pages 源）
- 但如果脚本报告成功而实际未更新 gh-pages，验证：`curl https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/gh-pages/data/proposals.json`
- 如果 gh-pages 过时但 master 已更新，使用 REST API 手动同步：使用正确 SHA 的 `PUT /repos/{owner}/{repo}/contents/data/proposals.json?ref=gh-pages`

### 处理重复的 Cron 超时事件

处理 cron 超时事件时：
1. 首先检查 `proposal-index.md` 状态是否已被之前的相同 cron 事件更新
2. 如果 PRD Confirmation 或 Technical Expectations 已显示 `timeout-approved`，不要再更新
3. 同一个 cron 事件可能多次到达；幂等性至关重要
4. 还要检查 `proposals.csv`——提案可能在 `proposal-index.md` 中但不在 CSV 中
5. **关键：检查实际字段值，而不仅仅是状态**——cron 可能说"PRD确认超时"，但 `prd_confirmation` 可能已经是 `confirmed`。cron 提示描述的是*预期*超时的内容，但 cron 触发时的数据控制着实际需要更新的内容。始终将实际 CSV 字段值与 cron 所说的应该更新的内容进行比较。

**要注意的混淆状态模式**：当 `prd_confirmation=confirmed` 但 cron 说"PRD确认超时"时，这意味着：
- cron 创建时参数错误，或者
- PRD 在 cron 创建和触发之间被确认了
- 在这种情况下，cron 仍应将状态更新为 `approved_for_dev`（如果尚未这样做），但不应重新确认已确认的字段。

### CSV 重复预防

通过 patch 工具向 `proposals.csv` 添加新条目时：
1. 首先验证 ID 不存在
2. 为 `old_string` 使用唯一上下文
3. 如果不小心创建了重复项，立即删除

## 模板

此技能期望 `$TEMPLATES_DIR/` 中有三个模板：

| Template | Purpose |
|----------|---------|
| request-intake-template.md | 初始提案注册，包含澄清字段和确认门控 |
| proposal-status-template.md | 状态追踪，包含相关资源、确认门控和返修意见 |
| acceptance-checklist-template.md | 结构化验收评审，包含功能/质量/交付清单 |

## 已知问题

| Issue | Reference |
|-------|-----------|
| sync-proposals-to-website.py 分组逻辑陷阱 | references/sync-script-pitfalls.md |
| references/vite-cache-issue.md | Vite 构建缓存问题 |
| references/bash-pitfalls.md | bash 脚本陷阱：`((var++))` 配合 `set -e`、cp -r 挂起、引号间距 |

## 关键：网站前端字段名 vs CSV 字段名

**网站 UI（`ProjectCard.jsx`）读取特定的 JSON 字段名。**

| CSV field | JSON field | Website "访问" button reads |
|-----------|-----------|---------------------------|
| `prj_url` | `prjUrl` | `prjUrl` ✅ (primary) |
| `git_repo` | `gitRepo` | `gitRepo` ✅ (fallback for "访问", also used for "仓库" button) |
| `local_path` | `localPath` | `localPath` ✅ (used elsewhere) |

**"访问" button 工作原理（2026-05-15 修复后）：**
```jsx
{(project.prjUrl || project.gitRepo) && (
  <button onClick={() => window.open(project.prjUrl || project.gitRepo, '_blank')}>
    访问
  </button>
)}
```
- **Primary**：`prjUrl`（GitHub Pages 部署 URL）
- **Fallback**：`gitRepo`（GitHub 仓库 URL）
- **"仓库" button**：始终使用 `gitRepo`

**调试模式——当 JSON 数据正确但 UI 不显示"访问"时：**
1. 检查网站源码：`curl -s https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/master/src/components/ProjectCard.jsx | grep -n "prjUrl"`
2. 验证已部署的 JSON：`curl -s https://raw.githubusercontent.com/YeLuo45/prj-proposals-manager/gh-pages/data/proposals.json`（绕过 Pages CDN）
3. 修复 ProjectCard.jsx，推送到 master，GitHub Actions 自动重建
4. 如果重建未更新 dist/asset hash，手动触发：`gh workflow run "Deploy to GitHub Pages"`

**GitHub Pages 部署在同步后更新很慢：**
- 即使同步脚本成功，GitHub Pages CDN 可能需要 1-2 分钟才能反映变化
- 始终使用 `raw.githubusercontent.com` 进行即时验证，而不是 `yeluo45.github.io`
- 如果 raw.githubusercontent 显示正确数据但 Pages 没有，等待 60秒 重试

**REST API 推送可能会破坏大 payload（>100KB）的 JSON：**
- 始终在本地验证 JSON 有效性：`python3 -c "import json; json.load(open('proposals.json'))"`
- 如果 GitHub 报告"Unterminated string"错误，JSON 在上传期间被破坏了
- 重试推送——GitHub 上的文件可能仍是旧的有效版本
- 对于大文件，优先使用同步脚本（`sync-proposals-to-website.py`）而不是原始 REST API 调用

## 参考资料

| Document | Description |
|----------|-------------|
| references/data-model.md | CSV 结构和字段验证 |
| references/data-recovery.md | 从数据损坏中恢复 |
| references/data-structure-gotchas.md | CSV-JSON 字段对齐 + 前端字段名调试 |
| references/website-sync.md | GitHub 同步架构 |
| references/sync-script-pitfalls.md | 同步脚本已知问题 |
| references/vite-cache-issue.md | Vite 构建缓存问题 |
