# GitHub Pages Setup Pages 失败与重试

## 问题

新创建的仓库启用 GitHub Pages workflow mode 后，首次 workflow run 在 "Setup Pages" 步骤失败，但重新运行（re-run）后成功。

## n8n-design 案例（2026-05-14）

1. REST API `POST /repos/{owner}/{repo}/pages` 返回 201，配置成功
2. 触发 workflow，job "Setup Pages" 失败
3. 手动 re-run 后，所有步骤成功，GitHub Pages 正常

```
Job: build-and-deploy
  Status: completed
  Conclusion: failure
  Failed step: Setup Pages (number: 3)
```

## 根因

GitHub Pages 配置的传播存在延迟。workflow 在 Pages 配置完全生效前就开始执行，导致 `actions/configure-pages@v4` 步骤找不到已配置的 Pages 设置。

## 解决

**立即重试（re-run）**，而不是修改任何配置：

```bash
# API 触发 re-run
curl -X POST \
  -H "Authorization: Bearer {token}" \
  "https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/rerun"
```

**验证方法**：
```bash
# 检查 latest run 状态
curl -s "https://api.github.com/repos/{owner}/{repo}/actions/runs" | jq '.workflow_runs[0] | {id, status, conclusion}'

# 等待完成（轮询）
for _ in $(seq 1 12); do
  sleep 5
  status=$(curl -s "https://api.github.com/repos/{owner}/{repo}/actions/runs" | jq -r '.workflow_runs[0].status')
  if [ "$status" = "completed" ]; then
    echo "Done: $(curl -s ... | jq -r '.workflow_runs[0].conclusion')"
    break
  fi
  echo "Status: $status..."
done
```

## 已知模式

| 场景 | 症状 | 解决 |
|------|------|------|
| 新仓库首次启用 Pages | Setup Pages 失败 | 立即 re-run |
| Pages 配置刚更改 | Setup Pages 失败 | 等待 30s 后 re-run |
| gh-pages branch 不存在 | workflow mode 下正常（不需要） | N/A |
| environment protection | workflow success 但 Pages 404 | 移除 job 内 environment 块 |

## Checklist

- [ ] Pages API 返回 201（build_type: workflow）
- [ ] 首次 workflow 失败于 Setup Pages
- [ ] 执行 re-run
- [ ] 验证 conclusion: success
- [ ] curl HTTP 200 on GitHub Pages URL
