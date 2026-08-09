# OpenClaw Gateway Launcher
# Auto-detects install directory from script location

$host.UI.RawUI.WindowTitle = "OpenClaw Gateway"

$baseDir = $PSScriptRoot
if (-not $baseDir) { $baseDir = $PWD.Path }

$env:NODE_HOME = Join-Path $baseDir "nodejs"
$env:PATH = "$env:NODE_HOME;" + $env:PATH

$env:OPENCLAW_HOME = $baseDir
Set-Location -Path $baseDir

$env:PATH = (Join-Path $baseDir "node_modules\.bin") + ";" + $env:PATH

Write-Host ""
Write-Host "========================================"
Write-Host "  OpenClaw Gateway - Starting..."
Write-Host "========================================"
Write-Host ""

Write-Host "[Env] Node.js:"
& node -v
Write-Host "[Env] OpenClaw:"
& openclaw --version
Write-Host "[Env] WorkDir: $PWD"
Write-Host "[Env] ConfigDir: $env:OPENCLAW_HOME\.openclaw"
Write-Host ""

Write-Host "[Start] Starting OpenClaw Gateway..."
Write-Host "[Start] WebChat: http://127.0.0.1:18789"
Write-Host "[Start] Press Ctrl+C to stop"
Write-Host ""

& openclaw gateway --port 18789 --verbose

Write-Host ""
Write-Host "Gateway exited. Press any key to close..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")