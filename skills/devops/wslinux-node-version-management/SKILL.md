---
name: wslinux-node-version-management
description: WSL Linux Node.js 版本管理 — nvm 安装、中国镜像、.npmrc 冲突、rolldown binding 问题解决
tags: [wsl, node, nvm, version-management]
created: 2026-05-03
---

# WSL Linux Node.js 版本管理（nvm）

## 场景
WSL 环境下管理多个 Node.js 版本，解决不同项目需要不同 Node 版本的问题。

## 安装 nvm

```bash
# 下载到文件再执行（避免 stderr 管道干扰）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install-nvm.sh > install-nvm.sh
bash install-nvm.sh

# 安装到 ~/.nvm
```

## 加载 nvm

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```

## 中国镜像（必须）

大陆网络直接下载 Node.js 极慢（300s 超时）。使用 npmmirror 镜像：

```bash
export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node/
nvm install 20   # 从 npmmirror 下载
nvm install 18
```

## .npmrc prefix 冲突（踩坑）

系统如果有 `~/.npmrc` 设置了 `prefix`，nvm 会报错：

```
Error: Your user's .npmrc file has a `globalconfig` and/or a `prefix` setting, which are incompatible with nvm.
```

解决：
```bash
mv ~/.npmrc ~/.npmrc.bak   # 临时移走
nvm use 20
# 用完后移回：mv ~/.npmrc.bak ~/.npmrc
```

常见冲突配置：
```
prefix=/home/hermes/.npm-global
```

## 常用命令

```bash
nvm install --lts       # 安装最新 LTS 版本
nvm install 20          # 安装指定版本
nvm alias default 20    # 设置默认版本（新建 shell 时使用）
nvm current             # 查看当前激活的版本

# 临时切换（当前 shell）
nvm use 20

# 项目级自动切换：创建 .nvmrc
echo "20" > /path/to/project/.nvmrc
cd /path/to/project
nvm use  # 自动读取 .nvmrc
```

## rolldown/Vite 构建问题

切换 Node 版本后，Vite 8 的 rolldown native binding 可能报错：

```
Cannot find native binding @rolldown/binding-linux-x64-gnu
Error: Cannot find module '../rolldown-binding.linux-x64-gnu.node'
```

解决：
```bash
rm -rf node_modules package-lock.json
npm install
```

## 版本策略建议

| 项目类型 | 建议版本 | 说明 |
|----------|----------|------|
| 旧项目（Vite 4） | Node 18 | 最稳定 |
| 新项目（Vite 6+） | Node 20 | Vite 6+ 要求 |
| 最新工具 | Node 22 | 前沿需要 |
| 固定工具链 | Node 18 | 保持系统默认 |

## 验证命令

```bash
node --version      # 查看当前版本
npm --version       # 查看 npm 版本
which node          # 确认 node 路径
nvm list            # 列出已安装版本
```
