# Launcher for LaoLiu AI Chat
$baseDir = "D:\龙虾"
$env:NODE_HOME = "$baseDir\nodejs"
$env:OPENCLAW_HOME = $baseDir
$env:OLLAMA_MODELS = "$baseDir\ollama-models"
$env:PATH = "$baseDir\nodejs;$baseDir\node_modules\.bin;$baseDir\ollama-app;$env:PATH"
Set-Location $baseDir

# Start Ollama server if not running
$ollamaRunning = $false
try {
    $null = Invoke-WebRequest "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
    $ollamaRunning = $true
} catch {}

if (-not $ollamaRunning) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "$baseDir\ollama-app\ollama.exe"
    $psi.Arguments = "serve"
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $psi.EnvironmentVariables["OLLAMA_MODELS"] = "$baseDir\ollama-models"
    $null = [System.Diagnostics.Process]::Start($psi)
    Start-Sleep -Seconds 3
}

$gwRunning = $false
try {
    $null = Invoke-WebRequest "http://127.0.0.1:18789/health" -TimeoutSec 2 -UseBasicParsing
    $gwRunning = $true
} catch {}

if (-not $gwRunning) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $psi.Arguments = "-ExecutionPolicy Bypass -NoProfile -Command `$env:NODE_HOME='$baseDir\nodejs'; `$env:OPENCLAW_HOME='$baseDir'; `$env:PATH='$baseDir\nodejs;$baseDir\node_modules\.bin;'+`$env:PATH; Set-Location '$baseDir'; openclaw gateway --port 18789"
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $null = [System.Diagnostics.Process]::Start($psi)

    $tries = 0
    while ($tries -lt 30) {
        try {
            $null = Invoke-WebRequest "http://127.0.0.1:18789/health" -TimeoutSec 2 -UseBasicParsing
            break
        } catch {
            $tries = $tries + 1
            Start-Sleep -Seconds 2
        }
    }
}

# Use pythonw.exe to avoid console window
$pythonw = Join-Path (Split-Path (Get-Command python.exe).Source) "pythonw.exe"
Start-Process $pythonw -ArgumentList "$baseDir\老六Chat.pyw" -WorkingDirectory $baseDir
