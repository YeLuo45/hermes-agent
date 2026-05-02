# Pending Todos — 待执行任务

## 当前环境限制

session 只有 `skill_manage` 可用，`todo` 和 `file` 工具不可用。Pending todos 无法写入 `proposal-index.md`。

**下次会话有完整工具时，先执行：**
1. 用 `file` 工具把这3项写入 `~/.hermes/proposals/proposal-index.md` 末尾（`## Todo` 标题下）
2. 执行推送
3. 验证

---

## 待写入的 Todo 项

```
## Todo

- [ ] P-20260422-002-sync — 网络恢复后推送 proposals.json 到 YeLuo45/proposals-manager:main/data/proposals.json（SHA: 17b159e06eb3f497618cc73f97af4cc0525e9ef0，本地 JSON 在 ~/.hermes/scripts/proposals.json）
- [ ] P-20260422-002-verify — 验证 Soul Shooter (P-20260422-002) 出现在 proposals-manager 网站
- [ ] P-20260422-002-deploy-verify — 确认 https://yeluo45.github.io/soulshooter/ 可访问
```

---

## 执行步骤（网络恢复后）

### Step 1: 确认网络
```bash
curl --max-time 5 https://api.github.com
```

### Step 2: 推送 proposals.json
```bash
gh api repos/YeLuo45/proposals-manager/contents/data/proposals.json \
  -X PUT -f message="sync: add Soul Shooter P-20260422-002" \
  -f content="$(cat ~/.hermes/scripts/proposals.json | base64)"
```

### Step 3: 验证
```bash
# 检查 proposals.json 内容
gh api repos/YeLuo45/proposals-manager/contents/data/proposals.json --jq '.content' | base64 -d | python3 -m json.tool | grep -A3 'P-20260422-002'

# 打开网站
open https://yeluo45.github.io/proposals-manager/
```

### Step 4: 标记完成
修改 `~/.hermes/proposals/proposal-index.md`，把3个 `[ ]` 改为 `[x]`
