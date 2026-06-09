# sync-proposals-to-website.py 的覆盖风险

## 核心风险

`sync-proposals-to-website.py` 的数据流向：

```
proposal-index.md (read)  →  GitHub data/proposals.json (write)
                                     ↓
local CSV files ← OVERWRITTEN by GitHub data (read from GitHub)
```

**GitHub 是 source of truth。** 脚本执行流程：
1. 读取 `proposal-index.md` → 推送到 GitHub `data/proposals.json`
2. 从 GitHub 拉取最新 `data/proposals.json` → 生成 `projects.csv`、`proposals.csv`、`project_proposal_mapping.csv`

**如果只通过 CLI 写入 CSV（不更新 proposal-index.md），下次 sync 时 GitHub 的旧数据会覆盖本地 CSV。**

## 正确的登记顺序（对于 CLI 写入）

```
1. python3 proposal_manager_cli.py project add --name <name> --git-repo <url>
   → 写入本地 projects.csv + proposals.csv
2. 手动追加提案条目到 proposal-index.md
3. python3 sync-proposals-to-website.py
   → 读取 proposal-index.md → 推送 GitHub → 生成 CSV（CSV 被 GitHub 数据覆盖，但内容一致）
```

## 错误的登记顺序

```
1. python3 proposal_manager_cli.py project/proposal add
   → 写入 CSV
2. sync（不更新 proposal-index.md）
   → GitHub 拉取旧数据 → 覆盖本地 CSV
   → 新登记的项目/提案丢失
```

## 验证命令

```bash
# 检查 shannon-design 是否在 CSV 中
grep -i shannon ~/.hermes/proposals/projects.csv

# 检查 GitHub proposals.json（最终验证）
GH_TOKEN=$(grep github.com ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
curl -s -H "Authorization: token $GH_TOKEN" \
  "https://api.github.com/repos/YeLuo45/prj-proposals-manager/contents/data/proposals.json" | \
  python3 -c "import json,sys,base64; d=json.load(sys.stdin); print([p['name'] for p in json.loads(base64.b64decode(d['content']).decode()).get('projects',[]) if 'shannon' in p.get('name','').lower()])"
```

## 重复项目名冲突处理

sync 时如果 `proposal-index.md` 中有多个项目名相同的条目（如 `card-game-prototype`），脚本自动保留最早创建的那个，删除其余重复项。

因此 `proposal-index.md` 中的项目名必须唯一。
