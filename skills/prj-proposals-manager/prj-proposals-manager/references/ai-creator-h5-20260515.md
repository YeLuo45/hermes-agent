# ai-creator-h5 项目迭代记录

## 2026-05-15 视频生成功能迭代

### 需求
boss 选方向 A：多模态增强，新增 video-01 视频生成。

### 改动清单
| 文件 | 改动 |
|------|------|
| `src/adapter/MiniMaxAdapter.js` | 新增 `MiniMaxVideoAdapter`（video-01） |
| `src/services/videoService.js` | 新建，封装视频生成 + localStorage |
| `src/pages/generate.js` | 新增"视频"tab |
| `src/pages/history.js` | 支持视频历史 |
| `package.json` | vite 版本升至 ^5.4.21 |

### commit
- `dfa5f4e` feat: add video generation (video-01) with duration selection

### 部署问题

**现象**：GitHub Pages 使用 legacy workflow（`dynamic/pages/pages-build-deployment`），push 到 master 后 gh-pages 分支未更新，线上还是旧版本。

**根因**：legacy workflow 不支持 workflow_dispatch，无法手动触发 rebuild。

**解决方案**：
1. 在项目根目录创建 `.github/workflows/deploy.yml`（GitHub Actions workflow mode），push 后自动触发
2. 或者手动在 GitHub Actions 页面 re-run workflow

**识别方式**：
```bash
gh api repos/{owner}/{repo}/pages  # build_type: "legacy" = legacy workflow
```

**正确做法**：新项目部署时使用 GitHub Actions workflow mode（`build_type: "workflow"`），不要用 legacy。

### 流程问题

本次迭代违反了高速迭代原则——没有先登记提案就直接 dev。导致：
- 代码已 commit push，但提案状态无法追踪
- proposals 网站无法同步本次交付

**正确做法**：即使是极小的功能迭代，也要先在 proposal-index.md 登记，注明"高速迭代模式"，再推进开发。

## 2026-05-15 B系列用户体验增强迭代

### 需求
boss 选方向 B1→B2→B3→B4→B5 全部实现。

### 改动清单
| 优先级 | 功能 | 核心文件 |
|--------|------|----------|
| P0 | B1: 骨架屏 + 生成进度反馈 + 失败重试 | generate.js, app.js, global.css |
| P1 | B2: 空状态引导 + API Key提示 + 示例prompt | generate.js, history.js |
| P2 | B3: 移动端优化 + 图片手势缩放 + 分享 | app.js, my.js, global.css |
| P3 | B4: 浅色/深色/跟随系统主题切换 | app.js, my.js, global.css |
| P4 | B5: 离线检测 + 重试队列 + 本地缓存 | app.js |

### commit
- `05a7cd7` feat: B1-B5 UX enhancements
- `3df2fad` test: add vitest unit tests for adapter, videoService, app

### 测试文件（subagent创建）
```
tests/
├── setup.js              # Mock localStorage/fetch/online/offline/matchMedia
├── adapter.test.js       # MiniMaxAdapter 全模型测试（479行）
├── videoService.test.js  # 视频service测试
└── app.test.js           # 进度/重试/主题/离线检测测试
```

### npm install 问题（持续存在）
- `npm install` 始终返回 "up to date, audited 1 package"
- package-lock.json 声明57个包，但 node_modules 实际只有 @esbuild/@rollup/@types
- vite 目录存在 lock 但不存在 node_modules
- 原因：subagent commit 时删除了 package-lock.json，npm ci 认为状态正常但实际未安装
- 解决方案：re-add package-lock.json 后再 npm install，或手动 npm install -D vitest

### GitHub Pages 部署选项
| 方式 | 操作 | 适用场景 |
|------|------|----------|
| 选择1 | GitHub Actions 页面手动 Re-run | legacy workflow（无workflow_dispatch） |
| 选择2 | 添加 .github/workflows/deploy.yml | 新workflow，可自动触发 |

### Test Agent 局限性
- subagent 能创建测试文件（质量良好）
- 但无法运行 `vitest run --coverage` 验证覆盖率
- npm install 网络问题是 blocker
- 建议：先确保 node_modules 正常，再委托 test agent
