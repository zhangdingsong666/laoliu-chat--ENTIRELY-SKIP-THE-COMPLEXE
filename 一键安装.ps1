# 老六 Chat — 一键安装
# 在文件夹地址栏输入 powershell 回车，然后输入 .\一键安装.ps1
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
Set-Location $scriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  老六 Chat 一键安装" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Python 依赖
Write-Host "[1/2] 安装 Python 依赖..." -ForegroundColor Green
try {
    pip install --quiet pillow PyPDF2 python-docx openpyxl python-pptx 2>&1 | Out-Null
    Write-Host "  完成" -ForegroundColor Green
} catch {
    Write-Host "  失败 - 请确认已安装 Python（python.org 下载）" -ForegroundColor Red
}

# Node.js 依赖
Write-Host "[2/2] 安装 Node.js 依赖..." -ForegroundColor Green
try {
    npm install 2>&1 | Out-Null
    Write-Host "  完成" -ForegroundColor Green
} catch {
    Write-Host "  失败 - 请确认已安装 Node.js（nodejs.org 下载）" -ForegroundColor Red
}

Write-Host ""
Write-Host "安装完成！" -ForegroundColor Yellow
Write-Host "以后启动方式：文件夹地址栏输 powershell → .\一键启动.ps1" -ForegroundColor Gray
Write-Host ""
Read-Host "按回车关闭窗口"
