# Proposal Index 维护规范

## 插入新提案的正确方法

**不要用 patch**：proposal-index.md 有大量相似的元数据行，patch 经常匹配到多个位置。

**用 execute_code 按行号精确操作**：

```python
content = open('/home/hermes/.hermes/proposals/proposal-index.md').read()
lines = content.split('
')

# 1. 找到目标位置
for i, line in enumerate(lines):
    if 'P-20260503-023: TodoList V15' in line:
        v15_pos = i
    if '- `Last Update`: 2026-05-03' in line and i > v15_pos:
        last_up = i
        break

# 2. 找到目标行后面的 "---" 分隔符
sep = last_up + 1
while not lines[sep].startswith('---'):
    sep += 1

# 3. 构建新条目，插入
new_section = '...V16 entry content...'
new_lines = lines[:last_up] + [new_section] + lines[sep+1:]
open('/home/hermes/.hermes/proposals/proposal-index.md', 'w').write('
'.join(new_lines))
```

## 分隔符缺失 Bug

proposal-index.md 各提案块之间必须有 `\n\n---\n` 分隔符（**两个换行**）。

**检查方法：**
```bash
grep -n 'P-' ~/.hermes/proposals/proposal-index.md
# 正常：两个提案ID之间隔着 ---
# 异常：提案A结束后直接跳到提案B标题，中间没有 ---
```

**修复方法（patch 失效时用 standalone 脚本）：**
```python
content = open('/home/hermes/.hermes/proposals/proposal-index.md').read()
old = '`Acceptance`: accepted\n\n### P-YYYYMMDD-NNN: 下一提案标题'
new = '`Acceptance`: accepted\n\n---\n\n### P-YYYYMMDD-NNN: 下一提案标题'
if old in content:
    content = content.replace(old, new, 1)
    open('/home/hermes/.hermes/proposals/proposal-index.md', 'w').write(content)
    print('Separator fixed!')
```

**patch 工具失效的典型错误：**
- `"Found N matches for old_string. Provide more context..."` → 添加更多上下文
- `"old_string and new_string are identical"` → 替换未执行，需要用上述 Python 脚本

## 快速检查命令

```bash
# 检查是否有重复的提案标题
grep -n "^### P-20260503-02" ~/.hermes/proposals/proposal-index.md

# 检查版本号顺序
grep "^### P-20" ~/.hermes/proposals/proposal-index.md | grep TodoList | awk '{print $2, $3}'
```

---

# btoa/atob 中文编码修复（高优先级）

## 问题

GitHub API 返回的 base64 内容用 `atob()` 解码会破坏 UTF-8 中文。`atob()` 假设 Latin-1 编码。

## 修复

**读取时（atob → 解码）：**
```javascript
// ❌ 错误 — 中文乱码
const content = atob(data.content)

// ✅ 正确 — UTF-8 中文正常
const content = decodeURIComponent(escape(atob(data.content)))
```

**写入时（编码 → btoa）：**
```javascript
// ❌ 错误
const encoded = btoa(JSON.stringify(newData))

// ✅ 正确
const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(newData))))
```

## 影响范围

- `useGitHub.js` — 网站数据读取
- `useTodos.js` — 看板数据读取

## 验证

```bash
# 部署后检查 JS bundle
grep -o 'decodeURIComponent(escape(atob' dist/static/js/*.js
```
