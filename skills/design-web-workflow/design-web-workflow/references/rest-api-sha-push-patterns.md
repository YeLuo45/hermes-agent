# REST API Push: SHA Conflict Patterns & Resolution

本参考文件沉淀自设计文档站项目的 GitHub REST API 推送经验。

---

## 1. 核心模式：SHA-first PUT /contents

每次 `PUT /repos/{owner}/{repo}/contents/{path}` 都必须先获取目标文件的当前 SHA（如果文件已存在），否则返回 `409 Conflict`。

```python
def push_file(path, content):
    # Step 1: 获取当前 SHA（如果文件存在）
    sha = None
    try:
        req = urllib.request.Request(f'{BASE}/repos/{OWNER}/{REPO}/contents/{path}',
                                     headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            existing = json.loads(r.read())
            sha = existing.get('sha')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sha = None  # 文件不存在，不需要 SHA
        else:
            raise

    # Step 2: 推送（含 SHA 处理 409）
    encoded = base64.b64encode(content.encode()).decode()
    data = {'message': f'docs: add {path}', 'content': encoded, 'branch': 'main'}
    if sha:
        data['sha'] = sha

    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload,
                                headers={**HEADERS, 'Content-Type': 'application/json'},
                                method='PUT')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())
```

---

## 2. 409 Conflict 的三种场景

| 场景 | 错误信息 | 原因 | 解决 |
|------|----------|------|------|
| 文件存在但未传 SHA | `reference already exists` | 直接 PUT 未获取 SHA | 先 GET 获取 SHA |
| 文件不存在但传了 SHA | `"sha" wasn't supplied` | 凭空传了不存在的 SHA | 去掉 sha 字段 |
| 目录已存在作为文件 | `reference already exists` | path 冲突 | GET 确认后决定 |

---

## 3. 常见推送失败与修复

### 3.1 `{"error": "reference already exists", "code": 409}`

**场景**：首次推送 `docs-site/.vitepress/config.mjs` 时返回 409，但该文件在 GitHub 上实际不存在。

**根因**：推送 `README.md` 时触发了 `docs-site/` 目录的创建。之后尝试在同一 commit 内推送 `docs-site/.vitepress/config.mjs` 时，API 认为"引用已存在"（目录已存在作为文件路径的一部分）。

**解决**：分两次推送，或者先分别推送各目录层级：

```python
# 正确顺序：先叶子文件，后目录
# 第一次推送：建立目录结构
for leaf_file in ['docs-site/.vitepress/public/logo.svg',
                  'docs-site/.vitepress/theme/index.js']:
    api_put(leaf_file, content)  # 会自动创建父目录

# 第二次推送：其他文件
for f in remaining_files:
    api_put(f, content)
```

### 3.2 `{"error": "\"sha\" wasn't supplied", "code": 422}`

**场景**：某些文件（如 `.github/workflows/vitepress-pages.yml`）推送时报 422。

**根因**：GitHub 认为该 path 已有内容但 PUT 请求没有提供 SHA。可能是之前的推送部分成功。

**解决**：加上 SHA 参数：

```python
# 先 GET 获取 SHA
req = urllib.request.Request(f'{BASE}/repos/{OWNER}/{REPO}/contents/{path}',
                             headers=HEADERS)
with urllib.request.urlopen(req, timeout=8) as r:
    sha = json.loads(r.read()).get('sha')
api_put(path, content, sha=sha)  # 传 SHA
```

### 3.3 推送后文件不在预期目录

**场景**：推送 `docs-site/package.json` 后，文件出现在 repo 根目录而非 `docs-site/package.json`。

**根因**：`PUT /contents/{path}` 中的 `path` 参数直接决定文件位置。如果 path 是 `package.json`，文件就出现在根目录。

**解决**：在所有 path 前加目标子目录前缀：

```python
# ✅ 正确
api_put(f'docs-site/{relpath}', content)  # → docs-site/package.json

# ❌ 错误
api_put(relpath, content)  # → package.json（根目录）
```

已知受影响的仓库：media-crawler-design。

---

## 4. 批量推送优化

### 4.1 预取所有 SHA（减少 API 调用）

```python
# 先批量 GET 所有文件的 SHA
shas = {}
for rel in files_to_push:
    url = f'{BASE}/repos/{OWNER}/{REPO}/contents/{rel}'
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            shas[rel] = json.loads(r.read()).get('sha')
    except:
        shas[rel] = None

# 再批量推送
for rel, sha in shas.items():
    with open(f'{BASE_DIR}/{rel}') as f:
        content = f.read()
    api_put(rel, content, sha=sha)
```

### 4.2 并行推送（io-bound）

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(push_one, rel) for rel in sorted(files)]
    results = [f.result() for f in as_completed(futures)]
```

注意：并行度不要超过 5，避免触发 GitHub API 限流。

---

## 5. 推送失败自动处理

```python
def api_put_with_retry(path, content, sha=None, retries=3):
    for attempt in range(retries):
        try:
            encoded = base64.b64encode(content.encode()).decode()
            data = {'message': f'docs: add {path}', 'content': encoded, 'branch': 'main'}
            if sha:
                data['sha'] = sha
            payload = json.dumps(data).encode()
            req = urllib.request.Request(url, data=payload,
                                        headers={**HEADERS, 'Content-Type': 'application/json'},
                                        method='PUT')
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 409:
                # 文件存在但 SHA 未知，重新获取
                get_req = urllib.request.Request(f'{BASE}/repos/{OWNER}/{REPO}/contents/{path}',
                                                 headers=HEADERS)
                with urllib.request.urlopen(get_req, timeout=8) as r:
                    sha = json.loads(r.read()).get('sha')
                continue  # 重试
            if e.code == 422 and sha:
                # SHA 错误（文件不存在），去掉 SHA 重试
                sha = None
                continue
            raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise
    return {'error': 'max retries exceeded'}
```

---

## 6. 验证推送结果

```python
# 检查文件是否在正确位置
req = urllib.request.Request(f'{BASE}/repos/{OWNER}/{REPO}/contents/{path}', headers=HEADERS)
with urllib.request.urlopen(req, timeout=10) as r:
    item = json.loads(r.read())
    print(f"OK: {item['path']} sha={item['sha'][:8]}")
```

```bash
# 检查仓库根目录结构
curl -s "https://api.github.com/repos/{owner}/{repo}/contents/" \
  -H "Authorization: token $TOKEN" | jq '.[].name'
```
