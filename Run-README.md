# Hermes Agent 运行说明

## 一、结果概览

本次已在 `H:\WS\ai-tools\opensource\hermes-agent-src-20260411` 完成源码获取和基础运行验证。

- 目标仓库：`https://github.com/YeLuo45/hermes-agent.git`
- 当前机器上的 `git clone` / `git fetch` 会长时间卡住，因此本次改用 GitHub 源码压缩包完成源码落地
- 已创建 Python 虚拟环境：`.venv`
- 已完成基础依赖安装：`python -m pip install -e .`
- 已验证通过：
  - `python -m hermes_cli.main --help`
  - `python -m hermes_cli.main version`
  - `python -m hermes_cli.main doctor`（需启用 UTF-8 输出环境变量）

## 二、当前环境结论

- 仓库 README 明确写明：`Windows` 原生不受官方支持，推荐使用 `WSL2`
- 但在当前原生 Windows PowerShell 下，Hermes 的基础 CLI 已能启动
- 当前不能直接进入完整可用状态的主要原因不是代码崩溃，而是：
  - 尚未配置 `~/.hermes/.env`
  - 尚未完成 `hermes setup`
  - 当前终端默认编码是 `GBK`，`doctor` 的 Unicode 输出会报编码错误

## 三、已验证的命令

### PowerShell

```powershell
& ".\.venv\Scripts\python.exe" -m hermes_cli.main --help
& ".\.venv\Scripts\python.exe" -m hermes_cli.main version
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
& ".\.venv\Scripts\python.exe" -m hermes_cli.main doctor
```

### Bash / WSL

```bash
source .venv/Scripts/activate
python -m hermes_cli.main --help
python -m hermes_cli.main version
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m hermes_cli.main doctor
```

## 四、如何继续运行

### 方式一：继续在当前 Windows PowerShell 下做基础体验

```powershell
Set-Location "H:\WS\ai-tools\opensource\hermes-agent-src-20260411"
& ".\.venv\Scripts\python.exe" -m hermes_cli.main --help
& ".\.venv\Scripts\python.exe" -m hermes_cli.main version
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
& ".\.venv\Scripts\python.exe" -m hermes_cli.main doctor
& ".\.venv\Scripts\python.exe" -m hermes_cli.main setup
```

说明：

- `setup` 会引导你生成 `~/.hermes/.env` 和配置文件
- 没有 API Key 时，CLI 仍能启动，但很多工具不可用

### 方式二：按项目推荐，改到 WSL2 中运行

如果你后续想更接近官方支持路径，建议在安装了 Linux 发行版的 `WSL2` 环境里重新执行：

```bash
git clone https://github.com/YeLuo45/hermes-agent.git
cd hermes-agent
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
python -m hermes_cli.main doctor
```

说明：

- 当前机器上 `wsl.exe -l -v` 只看到 `docker-desktop`
- 这说明 `WSL2` 组件在，但还没有可用于日常开发的 Linux 发行版

## 五、当前已知问题

### 1. `git clone` / `git fetch` 卡住

表现：

- `git ls-remote` 正常
- 但 `git clone` 和 `git fetch` 卡在传输阶段

当前处理：

- 已改用 `codeload.github.com` 下载源码压缩包作为替代

### 2. `hermes doctor` 在默认 PowerShell 编码下报错

错误原因：

- 当前终端输出编码为 `GBK`
- `doctor` 输出里包含 Unicode 图标，导致 `UnicodeEncodeError`

解决方式：

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
& ".\.venv\Scripts\python.exe" -m hermes_cli.main doctor
```

### 3. `~/.hermes/.env` 尚未创建

这不是安装失败，而是首次配置尚未完成。

可执行：

```powershell
& ".\.venv\Scripts\python.exe" -m hermes_cli.main setup
```

## 六、Doctor 结果摘要

已确认：

- Python 可用
- 虚拟环境可用
- 核心 Python 依赖已安装
- `git`、`docker`、`node` 可见

尚未完成：

- `~/.hermes/.env`
- `config.yaml`
- 各类模型/API 密钥

可选缺失：

- `croniter`
- `python-telegram-bot`
- `discord.py`
- `rg`
- `agent-browser`
- `tinker-atropos` 子模块

## 七、停止与清理

当前没有持续运行的 Hermes 后台服务，无需额外停止。

如果只想删除本次 Python 环境：

### PowerShell

```powershell
Remove-Item -Recurse -Force ".\.venv"
```

### Bash / WSL

```bash
rm -rf .venv
```
