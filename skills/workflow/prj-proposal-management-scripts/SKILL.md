---
name: prj-proposal-management-scripts
description: 从 prj-proposal-management 技能中提取的所有脚本内容 — 包含 GitHub API 同步、Cron 定时任务创建、Git 部署命令
---

# prj-proposal-management 脚本集

## 1. GitHub API 同步到网站

### 同步 proposals.json 到 prj-proposals-manager

```python
# GET current file + SHA
GET https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json

# PUT new content with SHA (triggers GitHub Actions rebuild)
PUT https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json
body: { "message": "feat: add P-YYYYMMDD-XXX <name>", "content": <base64>, "sha": <sha> }
```

**注意**：网站 repo 是 `prj-proposals-manager`，不是 `proposals-manager`。同步脚本 `sync-proposals-to-website.py` 已配置正确目标。

### 修复 GitHub Repo 描述（中文）

```python
PATCH https://api.github.com/repos/YeLuo45/<repo>
body: { "description": "<Chinese description>", "homepage": "<pages-url>" }
```

---

## 2. Cron 定时任务创建

### PRD 确认倒计时

```python
cron(action='create',
     schedule='2026-04-16T12:43:00+08:00',
     prompt='【倒计时到期】提案 P-YYYYMMDD-XXX PRD确认超时，默认通过处理。请将 PRD Confirmation 更新为 timeout-approved 并继续技术诉求确认阶段。',
     name='P-YYYYMMDD-XXX-prd-confirm')
```

**参数说明**：
- `schedule`：ISO 时间戳格式，设置为当前时间 + 超时时长
- `prompt`：超时触发时执行的指令
- `name`：唯一标识，建议包含提案ID

### 技术诉求确认倒计时

```python
cron(action='create',
     schedule='2026-04-16T12:43:00+08:00',
     prompt='【倒计时到期】提案 P-YYYYMMDD-XXX 技术诉求确认超时，按当前明确假设默认通过。请将 Technical Expectations 更新为 timeout-approved 并输出技术方案。',
     name='P-YYYYMMDD-XXX-tech-confirm')
```

### 研究方向确认倒计时

```python
cron(action='create',
     schedule='2026-04-16T12:43:00+08:00',
     prompt='【倒计时到期】提案 P-YYYYMMDD-XXX 研究方向确认超时，Coordinator 自行决定下一迭代方向并推进。',
     name='P-YYYYMMDD-XXX-research-confirm')
```

---

## 3. Git 部署命令

### 克隆已有仓库（Step 1a）

```bash
git clone https://<token>@github.com/<owner>/<repo>.git ${DEV_OUTPUT_DIR}/<项目名>/proposals/
```

**使用 token**：`ghp_XXXXX`（YeLuo45）

### 创建部署分支

```bash
cd ${DEV_OUTPUT_DIR}/<项目名>/proposals
git checkout -b deploy/<项目名>-<YYYYMMDD>
```

### 提交部署

```bash
git add .
git commit -m "deploy: <项目名> P-YYYYMMDD-XXX"
git push -u origin deploy/<项目名>-<YYYYMMDD>
```

---

## 4. 完整部署流程脚本

```bash
# 1. 确定部署目标并创建部署分支
cd ${DEV_OUTPUT_DIR}/<项目名>/proposals
git checkout -b deploy/<项目名>-<YYYYMMDD>

# 2. 准备部署（React/Vite 项目）
npm run build  # 确保构建成功

# 3. 提交
git add .
git commit -m "deploy: <项目名> P-YYYYMMDD-XXX"

# 4. 推送
git push -u origin deploy/<项目名>-<YYYYMMDD>
```

---

## 5. 同步到 proposals-manager 网站

```python
# 1. 下载当前 proposals.json
GET https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json

# 2. 更新内容后上传
PUT https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json
body: {
    "message": "feat: update proposals P-YYYYMMDD-XXX",
    "content": <base64_encoded_json>,
    "sha": <sha_from_step1>
}

# 3. 触发 GitHub Actions rebuild（上传到 public/data/proposals.json）
# 下载更新的 proposals.json 到 public/data/proposals.json
# 然后 npm run build && gh-pages deploy
```

---

## 6. 查询 next proposal ID

从 `proposal-index.md` 读取今日最高 XXX 编号：

```bash
grep "P-$(date +%Y%m%d)" proposal-index.md | grep -oP 'P-\d{8}-\K\d+' | sort -n | tail -1
```
