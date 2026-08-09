# Install dependencies for desktop-control skill
Write-Output "Installing Python dependencies for desktop-control..."
Write-Output ""

# Ensure target directory exists
$targetDir = "D:\龙虾\python-libs"
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

# Install pyautogui and mss
pip install --target $targetDir pyautogui mss 2>&1 | ForEach-Object {
    if ($_ -match "Successfully installed") {
        Write-Output "SUCCESS: $_"
    } elseif ($_ -match "already satisfied") {
        Write-Output "SKIP: $_"
    }
}

Write-Output ""
Write-Output "Desktop-control dependencies installed to: $targetDir"
Write-Output "Add to PYTHONPATH: `$env:PYTHONPATH = '$targetDir'"
