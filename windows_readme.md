# Hermes Agent Windows 运行说明

## 1. 本次验证结论

已在 `H:\WS\ai-tools\opensource\hermes-agent-src-20260411` 的原生 Windows PowerShell 环境完成最小可运行验证，并补充了 Windows 启动封装脚本。

- 已通过的命令：
  - `& ".\.venv\Scripts\python.exe" -m hermes_cli.main --help`
  - `& ".\.venv\Scripts\python.exe" -m hermes_cli.main version`
  - `& ".\.venv\Scripts\python.exe" -m hermes_cli.main doctor`
  - `& ".\.venv\Scripts\python.exe" -m hermes_cli.main status`
- 结论：
  - Hermes CLI 在当前 Windows 环境下可以启动
  - 当前源码目录已经具备可执行的 Python 虚拟环境 `.venv`
  - 现在可以优先通过 `.\hermes.ps1` 或 `hermes.cmd` 简化启动
  - 目前还没有配置可用的模型凭据，所以还不能直接进行真实对话

## 2. 官方支持情况

项目 `README.md` 明确说明：

- 原生 Windows **不是官方支持平台**
- 官方推荐使用 `WSL2`

但从这次实际验证来看，Hermes 的基础 CLI 在当前 Windows PowerShell 中是可以正常启动和执行诊断命令的。

## 3. 当前机器上的实际状态

### 环境

- PowerShell：`5.1.26100.7920`
- Python：`3.14.4`
- Node.js：`v24.14.1`
- `uv`：当前 PowerShell 中未找到

### 项目状态

- 项目根目录已有 `.venv`
- `hermes-agent` 已经处于可执行状态
- `~/.hermes/.env` 存在
- `~/.hermes/config.yaml` 存在

### `hermes status` 结果摘要

- Model：`MiniMax-M2.7`
- Provider：`MiniMax`
- Terminal backend：`local`
- Gateway service：当前平台不支持服务管理
- 所有 API Key 项当前均显示为未配置

这意味着：

- CLI 程序本身已经能跑
- 但默认模型虽然被选中了，实际凭据并没有配置好
- 如果现在直接进入聊天，通常会卡在模型认证或调用阶段

## 4. 本次实际执行的命令

在项目目录中执行：

```powershell
Set-Location "H:\WS\ai-tools\opensource\hermes-agent-src-20260411"
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

& ".\.venv\Scripts\python.exe" -m hermes_cli.main --help
& ".\.venv\Scripts\python.exe" -m hermes_cli.main version
& ".\.venv\Scripts\python.exe" -m hermes_cli.main doctor
& ".\.venv\Scripts\python.exe" -m hermes_cli.main status
```

## 5. 推荐启动方式

项目根目录新增了两个 Windows 启动入口：

- `hermes.ps1`：适合 PowerShell
- `hermes.cmd`：适合 `cmd`，也可以在 PowerShell 中调用

这两个入口会自动完成以下事情：

- 优先使用项目内的 `.\.venv\Scripts\python.exe`
- 自动设置 `PYTHONUTF8=1`
- 自动设置 `PYTHONIOENCODING=utf-8`
- 将参数转发给项目根目录的 `hermes` 启动入口

以后优先使用下面这种短命令，不必每次手动写一长串 Python 路径和环境变量。

### PowerShell

```powershell
Set-Location "H:\WS\ai-tools\opensource\hermes-agent-src-20260411"
.\hermes.ps1
.\hermes.ps1 status
.\hermes.ps1 doctor
.\hermes.ps1 setup
.\hermes.ps1 model
.\hermes.ps1 auth
```

### CMD 或通用入口

```bat
cd /d H:\WS\ai-tools\opensource\hermes-agent-src-20260411
hermes.cmd
hermes.cmd status
hermes.cmd doctor
hermes.cmd setup
```

## 6. 如何在 Windows 下继续使用

### 方式一：继续用当前 PowerShell 做基础配置

先进入项目目录：

```powershell
Set-Location "H:\WS\ai-tools\opensource\hermes-agent-src-20260411"
```

先检查 CLI：

```powershell
.\hermes.ps1 --help
.\hermes.ps1 status
```

然后做首次配置：

```powershell
.\hermes.ps1 setup
```

如果你想手动切换模型或登录：

```powershell
.\hermes.ps1 model
.\hermes.ps1 auth
```

当模型凭据配置完成后，再启动交互式 CLI：

```powershell
.\hermes.ps1
```

## 7. 当前阻塞点

目前不是“项目跑不起来”，而是“项目已经能启动，但还不能真正工作”。

主要阻塞点有这些：

1. `hermes status` 显示已选择 `MiniMax-M2.7`，但对应凭据未配置。
2. `doctor` 提示仍需要执行 `hermes setup` 来补全完整工具访问配置。
3. `doctor` 还提示以下可选项未满足：
   - `rg` 未安装
   - `agent-browser` 未安装
   - `tinker-atropos` 子模块未初始化

这些不一定阻止 CLI 启动，但会影响部分高级功能。

## 8. 常用命令

### 查看版本

```powershell
.\hermes.ps1 version
```

### 查看诊断

```powershell
.\hermes.ps1 doctor
```

### 查看状态

```powershell
.\hermes.ps1 status
```

### 运行首次配置

```powershell
.\hermes.ps1 setup
```

### 启动聊天界面

```powershell
.\hermes.ps1
```

### 底层原始命令（排障备用）

如果封装脚本异常，也可以退回到底层命令：

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
& ".\.venv\Scripts\python.exe" -m hermes_cli.main status
```

## 9. 如果你想走官方推荐路径

如果你后续要长期稳定使用，建议改到 `WSL2` 中运行，因为这是项目 README 明确推荐的环境。

官方风格的典型流程是：

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
python -m hermes_cli.main doctor
```

## 10. 终端（Terminal）工具完整修复记录

### 问题现象
终端工具报错：`WSL ERROR: CreateProcessCommon:800: execvpe(/bin/bash) failed: No such file or directory`

### 根本原因
`_find_bash()` 在 `tools/environments/local.py` 和 `tools/process_registry.py` 中只查找标准路径：
- `C:\Program Files\Git\bin\bash.exe`
- `C:\Program Files (x86)\Git\bin\bash.exe`
- `$env:LOCALAPPDATA\Programs\Git\bin\bash.exe`

但本机 Git 安装在非标准路径：**`H:\Program Files\Git\bin\bash.exe`**，导致查找失败。

### 修复方案
已更新 `hermes.ps1`，加入 Git Bash 自动探测逻辑（包含 `H:\` 盘符）：

```powershell
# Auto-detect Git Bash on Windows (required for terminal tool)
if ($null -eq $env:HERMES_GIT_BASH_PATH -or $env:HERMES_GIT_BASH_PATH -eq "") {
    $gitBashPaths = @(
        "H:\Program Files\Git\bin\bash.exe",    # 非标准安装位置优先
        "C:\Program Files\Git\bin\bash.exe",
        "C:\Program Files (x86)\Git\bin\bash.exe",
        "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
    )
    foreach ($gitBashPath in $gitBashPaths) {
        if (Test-Path $gitBashPath) {
            $env:HERMES_GIT_BASH_PATH = $gitBashPath
            break
        }
    }
}
```

### 验证结果（2026-04-14）
- ✅ `terminal` 工具：`hermes doctor` 显示 `✓ terminal`
- ✅ 普通命令（echo/pwd/python --version/ls）：全部 exit_code=0
- ✅ PTY 模式（`pty=true`，用于交互式 REPL）：已安装 `pywinpty 3.0.3`，测试通过
- ⚠️ 注意：pywinpty 从 PyPI 直接下载极慢（~20KB/s），需要使用国内镜像：
  ```powershell
  pip install pywinpty -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
  ```

### 手动指定 Git Bash 路径（如需）
若 `hermes.ps1` 仍未找到，可手动设置环境变量：
```powershell
$env:HERMES_GIT_BASH_PATH = "H:\Program Files\Git\bin\bash.exe"
```

---

## 11. 一句话总结

当前这份 Hermes Agent 源码已经在你的 Windows PowerShell 上成功跑通了 CLI 启动与诊断流程；现在可以优先通过 `.\hermes.ps1` 或 `hermes.cmd` 进行简化启动，下一步只需要完成 `hermes setup` / `hermes model` 的凭据配置，才能真正进入可用的聊天状态。
