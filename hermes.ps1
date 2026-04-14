[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$HermesArgs
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$launcher = Join-Path $projectRoot "hermes"

if (-not (Test-Path $pythonExe)) {
    throw "Missing virtual environment Python: $pythonExe"
}

if (-not (Test-Path $launcher)) {
    throw "Missing Hermes launcher: $launcher"
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Auto-detect Git Bash on Windows (required for terminal tool)
if ($null -eq $env:HERMES_GIT_BASH_PATH -or $env:HERMES_GIT_BASH_PATH -eq "") {
    $gitBashPaths = @(
        "H:\Program Files\Git\bin\bash.exe",
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

& $pythonExe $launcher @HermesArgs
$exitCode = $LASTEXITCODE

if ($null -ne $exitCode) {
    exit $exitCode
}
