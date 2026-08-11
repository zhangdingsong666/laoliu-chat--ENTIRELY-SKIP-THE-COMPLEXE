# 老六 Chat — 启动
# 在文件夹地址栏输入 powershell 回车，然后输入 .\一键启动.ps1
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
Set-Location $scriptDir

# ---- 桌面快捷方式（首次运行自动创建）----
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktop\老六Chat.lnk"
$ps1Path = "$scriptDir\一键启动.ps1"

if (-not (Test-Path $shortcutPath)) {
    try {
        $ws = New-Object -ComObject WScript.Shell
        $s = $ws.CreateShortcut($shortcutPath)
        $s.TargetPath = "powershell.exe"
        $s.Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$ps1Path`""
        $s.WorkingDirectory = $scriptDir
        $s.Description = "老六 Chat - AI 桌面助手"
        $s.IconLocation = "$scriptDir\app-icon.ico"
        $s.Save()
        Write-Host "桌面快捷方式已创建：老六Chat" -ForegroundColor Cyan
    } catch {
        Write-Host "快捷方式创建失败（不影响使用）" -ForegroundColor DarkGray
    }
}

# ---- 启动程序 ----
Write-Host "正在启动老六 Chat..." -ForegroundColor Green
try {
    Start-Process -FilePath pythonw -ArgumentList "老六Chat.pyw" -WindowStyle Hidden
    Write-Host "已启动！桌面应该能看到老六 Chat 窗口了" -ForegroundColor Yellow
} catch {
    Write-Host "启动失败，请确认已安装 Python" -ForegroundColor Red
}

Write-Host ""
Read-Host "按回车关闭窗口"
