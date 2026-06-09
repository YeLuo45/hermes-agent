# 导航栏统一规范

> 多页面文档站在并行 subagent 生成时，导航结构容易漂移。本参考文件定义标准模式和验证方法。

---

## 标准导航 HTML 模板

**适用项目**：hermes-agent-design、astrbot-design 等多页面纯 HTML 文档站。

```html
<!-- 标准导航：class="nav"，pipe 分隔，无 nav-inner/nav-brand -->
<div class="nav">
    <a href="index.html">首页</a> |
    <a href="api.html">API</a> |
    <a href="dashboard.html">Dashboard</a> |
    <a href="mcp.html">MCP</a> |
    <a href="agent-runner.html">Agent Runner</a> |
    <a href="platform-adapter.html">平台适配器</a> |
    <a href="plugin-development.html">插件开发</a>
</div>
```

**对应 CSS**：
```css
.nav { background: #1a1a2e; padding: 15px 20px; text-align: center; border-bottom: 1px solid #2a2a4a; }
.nav a { color: #00d4ff; text-decoration: none; margin: 0 15px; font-size: 0.95em; }
.nav a:hover { text-decoration: underline; }
.nav a.active { color: #fff; font-weight: bold; }
```

---

## 禁止模式（常见漂移来源）

| 模式 | 原因 | 修复 |
|------|------|------|
| `<nav class="nav">` + `.nav-inner/.nav-brand` | subagent 自由发挥加了品牌区 | 统一改为 `<div class="nav">` |
| `<nav class="navbar">` | 不同标签混用 | 统一改为 `<div class="nav">` |
| 无分隔符或不同分隔符 | 有的用 `|`，有的用空格 | 统一用 ` \| ` |
| SVG 图标/品牌文字 | dashboard.html 曾有 SVG logo | 删除，保持纯链接 |
| `class="active"` 当前页标记 | subagent 容易加在当前页 | 删除，统一无 active 标记 |

---

## 一致性验证测试

```python
def test_nav_consistency():
    """验证所有页面导航结构完全一致"""
    import requests
    
    BASE = "https://yeluo45.github.io/hermes-agent-design"
    PAGES = ['index.html', 'api.html', 'dashboard.html', 'mcp.html', 
             'agent-runner.html', 'platform-adapter.html', 'plugin-development.html']
    
    def get_nav_html(page):
        r = requests.get(f"{BASE}/{page}", timeout=10)
        content = r.text
        pos = content.find('class="nav"')
        if pos == -1:
            return None
        end = content.find('</div>', pos) + 6
        return content[pos:end]
    
    navs = {page: get_nav_html(page) for page in PAGES}
    
    # 无页面缺失 nav
    missing = [p for p, n in navs.items() if n is None]
    assert not missing, f"Pages missing nav: {missing}"
    
    # 所有 nav HTML 完全相同
    unique = set(navs.values())
    assert len(unique) == 1, f"Nav structures differ. Unique: {len(unique)}"
    
    # 验证标准模式
    index_nav = navs['index.html']
    assert 'class="nav"' in index_nav
    assert '|' in index_nav  # pipe 分隔符
    assert 'nav-inner' not in index_nav  # 无嵌套
    assert 'nav-brand' not in index_nav   # 无品牌
    
    print(f"PASS: All {len(PAGES)} pages have consistent navigation")
```

---

## subagent 导航交接检查清单

当用 subagent 并行生成多页面时，每个 subagent 交付后必须检查：

- [ ] 导航 HTML 使用 `<div class="nav">` 而非 `<nav>` 或其他标签
- [ ] 链接分隔符为 ` | `（pipe 前后有空格）
- [ ] 无 `.nav-inner`、`.nav-brand`、`.nav-links` 等嵌套元素
- [ ] 无 SVG 图标或品牌文字
- [ ] 无 `class="active"` 当前页标记
- [ ] 所有 7 个链接齐全（首页、API、Dashboard、MCP、Agent Runner、平台适配器、插件开发）
- [ ] 链接目标文件存在（`plugin-dev.html` 错误，正确为 `plugin-development.html`）

---

## 历史教训

**hermes-agent-design 导航漂移事件**：
- 初始：index.html 为简单链接，api/platform-adapter/plugin 用 `.nav-inner/.nav-brand`，dashboard 用 `.navbar+SVG`，mcp 用 `.navbar`，agent-runner 用 `<nav>`
- 根因：6 个 subagent 并行生成，各自加了"创意"
- 修复：将所有页面统一为 index.html 模式（简单链接 + pipe 分隔）
- 教训：并行 subagent 必须强制使用标准模板，不能自由发挥

**关键文件路径**：`/home/hermes/hermes-agent-design/`
