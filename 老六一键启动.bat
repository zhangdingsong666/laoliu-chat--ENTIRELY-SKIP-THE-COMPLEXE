@echo off
chcp 65001 >nul
title 老六 - 一键启动

REM 切换到脚本所在目录
cd /d "%~dp0"

echo.
echo ========================================
echo   老六 AI 助手 - 一键启动
echo ========================================
echo.

REM 设置环境变量（使用脚本所在目录）
set "NODE_HOME=%~dp0nodejs"
set "OPENCLAW_HOME=%~dp0"
set "PATH=%~dp0nodejs;%~dp0node_modules\.bin;%PATH%"

REM 0. Ollama（可选 — 仅视觉功能需要）
set OLLAMA_RUNNING=0
powershell.exe -Command "try { $r = Invoke-WebRequest 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%~dp0ollama-app\ollama.exe" (
        echo [启动] 正在启动 Ollama 视觉服务...
        set "OLLAMA_MODELS=%~dp0ollama-models"
        start "" /min "%~dp0ollama-app\ollama.exe" serve
        echo [等待] 等待 Ollama 加载模型（约10秒）...
        timeout /t 8 /nobreak >nul
    ) else (
        echo [跳过] Ollama 未安装，视觉功能将不可用
    )
) else (
    echo [OK] Ollama 已在运行
)

REM 1. 检查网关是否已在运行
powershell.exe -Command "try { $r = Invoke-WebRequest 'http://127.0.0.1:18789/health' -TimeoutSec 3 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] 网关已在运行
    goto launch_chat
)

REM 2. 启动网关（后台隐藏窗口）
echo [启动] 正在启动 OpenClaw 网关...
start "" /min powershell.exe -ExecutionPolicy Bypass -Command "& { $env:NODE_HOME='%~dp0nodejs'; $env:OPENCLAW_HOME='%~dp0'; $env:PATH='%~dp0nodejs;%~dp0node_modules\.bin;'+$env:PATH; Set-Location '%~dp0'; openclaw gateway --port 18789 }"

REM 3. 轮询等待网关就绪
echo [等待] 等待网关就绪...
:wait_loop
timeout /t 2 /nobreak >nul
powershell.exe -Command "try { $r = Invoke-WebRequest 'http://127.0.0.1:18789/health' -TimeoutSec 3 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 goto wait_loop

echo [OK] 网关就绪！

:launch_chat
REM 4. 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo.
    pause
    exit /b 1
)

REM 5. 启动聊天
echo [启动] 启动老六 Chat...
start "" pythonw.exe "%~dp0老六Chat.pyw"

echo [完成] 老六AI助手已启动！
echo.
timeout /t 3 /nobreak >nul
exit
