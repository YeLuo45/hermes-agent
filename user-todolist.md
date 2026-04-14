# 待办事项（需要你手动完成）

## 必须完成

- [ ] 运行 `& ".\.venv\Scripts\python.exe" -m hermes_cli.main setup`，生成 `~/.hermes/.env` 与配置文件
- [ ] 在 `~/.hermes/.env` 中至少配置一个可用的模型提供商密钥，例如 `OPENROUTER_API_KEY`
- [ ] 在 PowerShell 中运行 `doctor` 前先设置：
  - [ ] `$env:PYTHONUTF8='1'`
  - [ ] `$env:PYTHONIOENCODING='utf-8'`

## 建议完成

- [ ] 安装 `ripgrep`（`rg`），提升文件搜索能力
- [ ] 如需浏览器自动化，执行 `npm install` 安装 `agent-browser`
- [ ] 如需完整开发或官方支持路径，安装一个真正可用的 `WSL2` Linux 发行版，而不只是 `docker-desktop`
- [ ] 如需 RL 相关能力，执行 `git submodule update --init --recursive`
- [ ] 如果你希望保留 Git 历史而不是源码快照，后续在网络正常或 WSL 环境中重新执行 `git clone`

## 可选说明

- 当前目录 `H:\WS\ai-tools\opensource\hermes-agent-src-20260411` 是源码快照，不是完整 Git 工作树
- 本机原生 Windows 已能跑 `--help`、`version` 和 `doctor`
- 但项目官方仍建议在 `WSL2` 中使用
