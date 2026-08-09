param(
    [ValidateSet("describe", "find", "watch")]
    [string]$Action = "describe",
    [string]$Prompt = "",
    [int]$Interval = 5,
    [int]$Count = 1
)

$ErrorActionPreference = "Stop"
$captureScript = "D:\龙虾\skills\screen-insight\scripts\capture.ps1"
$ollamaApi = "http://127.0.0.1:11434/api/generate"
$model = "minicpm-v:8b"

function Get-Screenshot {
    $r = & powershell.exe -ExecutionPolicy Bypass -File $captureScript -Mode screen 2>$null
    $lines = $r -split "`n"
    $last = ($lines | Where-Object { $_ -match "\.png" } | Select-Object -Last 1).Trim()
    if ($last -and (Test-Path $last)) { return $last }
    return $null
}

function Invoke-Vision {
    param([string]$ImagePath, [string]$Query)

    if (-not (Test-Path $ImagePath)) {
        Write-Output "ERROR: Image not found: $ImagePath"
        return ""
    }

    # Read image as base64
    $bytes = [System.IO.File]::ReadAllBytes($ImagePath)
    $base64 = [System.Convert]::ToBase64String($bytes)

    $body = @{
        model = $model
        prompt = $Query
        images = @($base64)
        stream = $false
        options = @{
            num_gpu = 0
        }
    } | ConvertTo-Json -Depth 4

    try {
        $result = Invoke-RestMethod -Uri $ollamaApi -Method Post -Body $body -ContentType "application/json" -TimeoutSec 120
        return $result.response
    } catch {
        Write-Output "ERROR calling Ollama: $_"
        return ""
    }
}

switch ($Action) {
    "describe" {
        $query = if ($Prompt) { $Prompt } else { "Describe what you see on this screen in Chinese. List all visible windows, their approximate positions, text content, and any notable elements. Be concise." }

        Write-Output "Taking screenshot..."
        $img = Get-Screenshot
        if (-not $img) {
            Write-Output "ERROR: Failed to capture screenshot"
            exit 1
        }
        Write-Output "Screenshot: $img"
        Write-Output "Analyzing with Ollama ($model)..."
        $desc = Invoke-Vision $img $query
        Write-Output "--- Analysis ---"
        Write-Output $desc
        Write-Output "--- End ---"
    }

    "find" {
        $query = if ($Prompt) { "On this screen, find: $Prompt. Describe its exact location and approximate pixel coordinates." } else { "List all visible windows and UI elements with their approximate screen coordinates (x,y center)." }

        Write-Output "Taking screenshot..."
        $img = Get-Screenshot
        if (-not $img) {
            Write-Output "ERROR: Failed to capture screenshot"
            exit 1
        }
        Write-Output "Screenshot: $img"
        Write-Output "Searching for: $Prompt"
        $desc = Invoke-Vision $img $query
        Write-Output "--- Results ---"
        Write-Output $desc
        Write-Output "--- End ---"
    }

    "watch" {
        $query = if ($Prompt) { $Prompt } else { "Describe any changes on this screen compared to a normal desktop. Chinese." }

        Write-Output "Starting screen watch (every ${Interval}s, $Count times)..."
        for ($i = 1; $i -le $Count; $i++) {
            Write-Output "`n--- Frame $i/$Count ---"
            $img = Get-Screenshot
            if (-not $img) {
                Write-Output "ERROR: Screenshot failed at frame $i"
                continue
            }
            Write-Output "Screenshot: $img"
            $ts = Get-Date -Format "HH:mm:ss"
            $desc = Invoke-Vision $img "$query (timestamp: $ts)"
            Write-Output "[$ts] $desc"
            if ($i -lt $Count) {
                Write-Output "Waiting ${Interval}s..."
                Start-Sleep -Seconds $Interval
            }
        }
        Write-Output "Watch complete."
    }
}
