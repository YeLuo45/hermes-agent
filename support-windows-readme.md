# Windows 支持说明

本文档记录 Hermes Agent 在 Windows 环境下的已知问题和解决方案。

---

## 终端工具不工作的修复

### 问题现象

终端命令报错：
```
WSL ERROR: CreateProcessCommon:800: execvpe(/bin/bash) failed: No such file or directory
```

`hermes doctor` 显示 `terminal` 工具正常，但实际执行命令时报上面的错误。

### 根本原因

`_find_bash()` 在 `tools/environments/local.py` 和 `tools/process_registry.py` 中按以下顺序查找 Git Bash：

1. `C:\Program Files\Git\bin\bash.exe`
2. `C:\Program Files (x86)\Git\bin\bash.exe`
3. `%LOCALAPPDATA%\Programs\Git\bin\bash.exe`

如果 Git 安装在 **非标准路径**（如 `H:\Program Files\Git\...`），则找不到，终端工具完全失效。

### 解决方案

#### 方案一：使用 `hermes.ps1`（推荐）

项目根目录的 `hermes.ps1` 已包含 Git Bash 自动探测逻辑，会自动找到正确路径。直接使用：

```powershell
cd H:\WS\ai-tools\opensource\hermes-agent-src-20260411
.\hermes.ps1 status
.\hermes.ps1 doctor
.\hermes.ps1
```

#### 方案二：手动设置环境变量

```powershell
$env:HERMES_GIT_BASH_PATH = "完整路径\bash.exe"
```

#### 方案三：修改源码（不推荐）

修改 `tools/environments/local.py` 中的 `_find_bash()` 函数，增加 `H:\Program Files\Git\bin\bash.exe` 路径。但每次更新源码后需要重新应用。

---

## pywinpty 安装（可选）

### 作用

`pywinpty` 是 Windows 上的伪终端库，用于 `terminal_tool(pty=true)` 交互式 CLI 工具（如 Python REPL、Codex 等）。**不安装则普通命令不受影响**。

### 安装命令

使用国内镜像：
```powershell
pip install pywinpty -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

从 PyPI 官方直接安装可能极慢（~20KB/s），不建议使用。

### 验证安装

```python
import winpty
print(winpty.__version__)  # 应输出 3.0.3 或类似版本
```

---

## 已知限制

### 1. Windows 不是官方支持平台

项目 README 明确说明：
> 原生 Windows **不是官方支持平台**，推荐使用 WSL2。

Windows 支持属于社区实验性实现。

### 2. `/dev/tty` 不可用

sudo 密码提权和交互式密码输入依赖 Unix `/dev/tty` 设备，在 Windows 上无法工作。如需 sudo 功能，配置 `SUDO_PASSWORD` 环境变量。

### 3. `os.setsid` 不可用

Windows 上跳过了 `preexec_fn=os.setsid`（进程组管理），子进程清理能力受限。

### 4. Git Bash 硬依赖

终端工具依赖 Git for Windows 的 Bash，不支持直接使用 `cmd.exe` 或 PowerShell 作为执行后端。

---

## 快速检查清单

运行以下命令确认终端工具状态：

```powershell
cd H:\WS\ai-tools\opensource\hermes-agent-src-20260411
.\hermes.ps1 doctor
```

确认以下项目：
- ✅ `terminal` — 如显示此则终端工具已注册
- ✅ `✓ git` — Git 命令可用

测试终端命令：
```python
# 在 hermes chat 中执行，或用 python -c 测试
from tools.terminal_tool import terminal_tool
result = terminal_tool("echo hello")
print(result)  # 应返回 exit_code=0
```

---

## 常用命令

```powershell
# 启动交互式对话
.\hermes.ps1

# 查看状态
.\hermes.ps1 status

# 诊断检查
.\hermes.ps1 doctor

# 配置模型
.\hermes.ps1 model

# 首次配置
.\hermes.ps1 setup
```

---

## 获取帮助

- 项目主页：https://github.com/NousResearch/hermes-agent
- 官方推荐使用 WSL2 以获得最佳体验
- 提交 Issue：https://github.com/NousResearch/hermes-agent/issues
