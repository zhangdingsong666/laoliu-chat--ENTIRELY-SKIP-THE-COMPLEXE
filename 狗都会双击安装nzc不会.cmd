@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===== LaoLiu Chat - Full Install =====
echo.

REM ---- Check / Install Python ----
where python >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Python found
) else (
    echo [..] Installing Python 3.12 via winget...
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel%==0 (
        echo [OK] Python installed
        echo PLEASE RESTART YOUR COMPUTER, then run this installer again.
        pause
        exit /b 0
    ) else (
        echo [FAIL] Cannot install Python automatically.
        echo Please download from https://python.org (check "Add to PATH")
        pause
        exit /b 1
    )
)

REM ---- pip install ----
echo [..] Installing Python packages...
pip install --quiet pillow PyPDF2 python-docx openpyxl python-pptx
if %errorlevel%==0 (echo [OK] Python packages installed) else (echo [WARN] Some packages may have failed)

REM ---- Check / Install Node.js ----
where node >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Node.js found
) else (
    echo [..] Installing Node.js LTS via winget...
    winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel%==0 (
        echo [OK] Node.js installed
        echo PLEASE RESTART YOUR COMPUTER, then run this installer again.
        pause
        exit /b 0
    ) else (
        echo [SKIP] Node.js not installed - red mode will not work
    )
)

REM ---- npm install ----
echo [..] Installing Node.js packages...
call npm install --no-audit --no-fund
if %errorlevel%==0 (echo [OK] Node.js packages installed) else (echo [WARN] Some packages may have failed)

echo.
echo ===== ALL DONE =====
echo Now double-click the LAUNCH cmd or vbs file to start!
pause