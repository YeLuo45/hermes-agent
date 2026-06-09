# REST API 分批推送：网络超时处理

## 问题

使用 REST API `PUT /repos/{owner}/{repo}/contents/{path}` 推送大量文件时（如 17 个文件），可能超时（300s limit）。

## ai-hedge-fund-design 案例

1. 第一次批量上传（os.walk 遍历 17 个文件）：超时（300s killed）
2. 第二次分两批上传：
   - 第一批（6 个优先文件）：34s 成功
   - 第二批（11 个剩余文件）：70s 成功

## 解决：优先级分批上传

```python
# 第一批：关键文件（README、workflow、入口配置）
priority = [
    ("README.md", "README.md"),
    (".github/workflows/vitepress-pages.yml", ".github/workflows/vitepress-pages.yml"),
    ("docs-site/package.json", "docs-site/package.json"),
    ("docs-site/index.md", "docs-site/index.md"),
    ("docs-site/.vitepress/config.mjs", "docs-site/.vitepress/config.mjs"),
]

# 第二批：其余文档
remaining = [
    "docs-site/architecture.md",
    "docs-site/agents.md",
    # ...
]
```

## 验证清单

```bash
# 确认所有文件已上传
curl -s "https://api.github.com/repos/{owner}/{repo}/git/trees/{sha}?recursive=1" | jq '.tree | length'

# 确认 .github/workflows 存在
curl -s "https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows"
```

## 性能参考

| 文件数 | 耗时 | 结果 |
|--------|------|------|
| 17 文件（单批） | 300s | 超时 killed |
| 6 文件（首批） | 34s | 成功 |
| 11 文件（次批） | 70s | 成功 |
