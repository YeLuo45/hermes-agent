# Hermes TodoList — GitHub Pages 部署版

## 访问地址

https://yeluo45.github.io/hermes-agent/

## 项目说明

本目录为 Hermes TodoList 的 GitHub Pages 静态部署产物，托管于 `gh-pages` 分支。

- 源码项目: `../todo-app/`
- 部署分支: `gh-pages`
- 技术栈: React 18 + Vite + localStorage

## 功能特性

- 新建 / 编辑 / 删除任务
- 标签管理（支持多标签）
- 截止日期设置
- 优先级提醒（P0/P1/P2/P3）
- 搜索与筛选（按创建日期/截止日期/优先级）
- 本地持久化存储（localStorage）

## 目录结构

```
./
├── index.html              # 入口 HTML
├── assets/                 # 构建资源
│   ├── index-*.js          # React 应用 bundle
│   └── index-*.css         # 样式文件
└── README.md               # 本文件
```

## 部署说明

本目录由 GitHub Actions 自动构建部署，触发条件：

- 推送至 `gh-pages` 分支
- 手动触发 `workflow_dispatch`

详见 `.github/workflows/deploy.yml`。

## 本地运行

如需本地预览构建产物：

```bash
# 使用任意静态服务器
npx serve .
# 或
python -m http.server 8080
```

然后访问 http://localhost:8080
