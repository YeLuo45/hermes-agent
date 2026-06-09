# VitePress 构建失败：Vue 解析器把 Markdown 中的 `<T>` 当成 HTML 标签

## 症状

VitePress 构建失败，报错：
```
SyntaxError: [plugin vite:vue] sdk.md (19:55): Element is missing end tag.
```

行号 19:55 指向 `### ModelPartial<T>` 标题，`ModelPartial` 被 Vue 编译器当成未闭合的 HTML 标签。

## 根因

VitePress 使用 Vue 编译器解析 Markdown，Markdown 中的 `<T>`、`TData>`、`TResult>` 等泛型语法会被 Vue 解析器当成 **HTML 开始标签**。如果对应的闭合标签不存在，编译失败。

## 受影响场景

- TypeScript 泛型语法：`interface Foo<T>`, `type Bar<T>`, `Partial<T>`
- 标题行包含 `<Letter>` 模式
- 代码块内的 `<T>` **不受影响**（在 fenced code block 中）
- 普通段落中的 `<T>` **不受影响**（不在标题中时可能侥幸通过，但标题行最危险）

## 修复方法

在标题行（`#`, `##`, `###`）中，将 `<` 转义为 `&lt;`：

```markdown
# 正确
### ModelPartial&lt;T>

# 错误
### ModelPartial<T>
```

对于普通段落中的泛型语法，如果担心可以也转义，但通常 Vue 解析器只严格检查标题行。

## 验证方法

构建前检查所有 Markdown 文件的标题行：

```bash
# 查找可能出问题的 <X> 模式（标题行中的单个大写字母）
grep -rn "^#.*<[A-Z]>\|^##.*<[A-Z]>\|^###.*<[A-Z]" docs-site/

# 或者查找所有含 <T 的标题（泛型相关）
grep -rn "^#.*<T\|^##.*<T" docs-site/
```

## 预防

在 subagent 的 `goal` prompt 中明确添加约束：

```
---
坑点：文档中禁止出现以下模式：
1. 标题行（# ## ###）包含未转义的 <T>、<TData> 等泛型语法
   → 必须写成 &lt;T&gt;、&lt;TData&gt;
2. 指向源码目录的相对路径（../../AGENTS.md、../docs/USERGUIDE 等）
3. 指向 docs-site/ 内不存在的图片路径和文档路径
图片使用 raw GitHub URL，不要用相对路径。
---
```

## 受影响项目记录

| 项目 | 文件 | 修复方式 |
|------|------|----------|
| minimax-cli-design | docs-site/sdk.md | `### ModelPartial<T>` → `### ModelPartial&lt;T>` |

---

## 案例 2：`{{ }}` 被当成 Vue 模板表达式

### 症状

VitePress 构建失败，报错：
```
[vite:vue] [plugin vite:vue] hooks.md (45:13): Error parsing JavaScript expression: Unexpected token (1:1)
```

行号 45 指向 JSON 配置中的 `"command": "echo 'About to run: {{.Tool}}'"`，`{{.Tool}}` 被 Vue 编译器当成模板表达式。

### 根因

VitePress 使用 Vue 编译器解析 Markdown，Markdown 中的 `{{variable}}` 模式会被当成 **Vue 模板语法**。如果 `variable` 不是合法的 JS 表达式，编译失败。

### 受影响场景

- Go 模板语法：`{{.Tool}}`, `{{.Input}}`, `{{.Session}}`
- Mustache 风格模板：`{{name}}`, `{{value}}`
- 双花括号任何用途（除代码块外）

### 修复方法

使用 HTML 实体转义：

```markdown
# JSON 中
"command": "echo 'About to run: &#123;&#123;.Tool&#125;&#125;'"

# 文档描述中
模板变量：
- `&#123;&#123;.Tool&#125;&#125;` — 工具名称
- `&#123;&#123;.Input&#125;&#125;` — 工具输入
```

注意：VitePress 模板转义（如 `{{` `"` }}`）在 JSON 字符串内无效，HTML 实体是唯一可靠方案。

### 验证方法

```bash
grep -rn "{{" docs-site/*.md
# 排除代码块内的 {{（在 ``` 之间）
```

### 受影响项目记录

| 项目 | 文件 | 修复方式 |
|------|------|----------|
| crush-design | docs-site/hooks.md | `{{.Tool}}` → `&#123;&#123;.Tool&#125;&#125;` |
