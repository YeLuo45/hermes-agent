# REST API 多目录推送：.github/ 遗漏问题

## 场景

当使用 REST API `PUT /repos/{owner}/{repo}/contents/{path}` 推送新仓库时，`os.walk()` 可能遗漏 `.github/` 等点目录。

## deepseek-tui-design 案例

1. 第一次上传：16 个文件（不含 `.github/workflows/`）
2. 检查 GitHub Actions → 无 workflow runs
3. 第二次上传：手动上传 `.github/workflows/vitepress-pages.yml`
4. GitHub Actions 检测到 workflow → 自动触发构建

## 教训

```python
# 正确做法：显式处理 .github 目录
for root, dirs, files in os.walk(project_root):
    if '.git' in root:
        continue
    for filename in files:
        filepath = os.path.join(root, filename)
        relpath = os.path.relpath(filepath, project_root)
        # 推送到 GitHub
```

## 验证清单

推送完成后验证：
```bash
# 检查 .github 目录是否在仓库中
curl -s "https://api.github.com/repos/{owner}/{repo}/contents/.github"

# 检查 workflow 是否被识别
curl -s "https://api.github.com/repos/{owner}/{repo}/actions/workflows" | jq '.workflows[].name'
```

## Workflow 自动触发条件

GitHub Actions workflow 被识别并触发需要：
1. 文件存在于 `.github/workflows/*.yml` 或 `.github/workflows/*.yaml`
2. workflow 语法正确（`name:` 字段存在）
3. 分支是 `main`（或 workflow 指定的分支）

---

## 陷阱：REST API 推送时子目录路径前缀丢失

**症状**：workflow 报错 `No such file or directory` 指向 `docs-site/`，但 GitHub 上文件存在。

**根因**：使用 `PUT /contents/{path}` 推送时，path 参数直接决定文件在仓库中的位置。
- `PUT .../contents/config.mjs` → 推到 repo 根目录
- `PUT .../contents/docs-site/config.mjs` → 推到 docs-site 子目录

如果 workflow YAML 中 `working-directory: ./docs-site`，但文件被推到根目录，checkout 后 `docs-site/` 就不存在。

**media-crawler-design 案例**：
1. 第一次推送：12 个文件散落在 repo 根目录（`.vitepress/`、`.github/`、`*.md`）
2. Workflow `working-directory: ./docs-site` → 找不到目录，构建失败
3. 修复：所有 path 前加 `docs-site/` 前缀重新推送，构建成功

**正确模式**：
```python
# 推送时显式加子目录前缀
docs_dir = "/path/to/project/docs-site"
for root, dirs, files in os.walk(docs_dir):
    for filename in files:
        local_path = os.path.join(root, filename)
        relpath = os.path.relpath(local_path, docs_dir)
        new_path = f"docs-site/{relpath}"  # ← 必须加子目录前缀
        api_put(new_path, content, f"docs: add {relpath}")
```

**验证推送结果**：
```python
# 检查 GitHub 上的文件树结构
GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1
# 确认文件在 docs-site/ 子目录下，而不是根目录
```
