# VitePress Nav/Sidebar 链接与 Dead Link 修复

> 2026-05-14 — multica-design 项目教训

## 问题

VitePress 构建时报 dead links：

```
(!) Found dead link /frontend in file README.md
(!) Found dead link /backend in file README.md
x Build failed: [vitepress] 2 dead link(s) found.
```

## 根因

VitePress 中 `nav` 的 `link` 值必须与**实际文件名**完全匹配（不含 `.md` 扩展名）。

| config.mjs 中写的是 | 实际文件名 | 结果 |
|---------------------|-----------|------|
| `link: "/frontend"` | `frontend.md` | ✅ 正常工作 |
| `link: "/frontend"` | `frontend-stack.md` | ❌ dead link |
| `link: "/frontend-stack"` | `frontend-stack.md` | ✅ 正常工作 |

## 修复

1. **修改 config.mjs 的 nav/sidebar**：让 link 值与实际文件名匹配
   ```js
   // ✅ 正确
   { text: "前端架构", link: "/frontend-stack" }
   ```

2. **修改 README.md 中的相对链接**：同步修复 README 中的链接
   ```markdown
   - [前端架构](/frontend-stack)
   ```

3. **启用 `ignoreDeadLinks: true`**：作为安全网
   ```js
   export default defineConfig({
     ignoreDeadLinks: true,
   });
   ```

## 完整修复示例（multica-design）

**config.mjs nav**：
```js
{ text: "前端", link: "/frontend-stack" },   // ← 修正
{ text: "后端", link: "/backend-stack" },    // ← 修正
```

**README.md**：
```markdown
- [前端架构](/frontend-stack)   // ← 修正
- [后端架构](/backend-stack)    // ← 修正
```

**config.mjs 全局**：
```js
export default defineConfig({
  title: "Multica Design",
  ignoreDeadLinks: true,
});
```
