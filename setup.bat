@echo off
chcp 65001 >nul
title 老六 Chat - 安装向导
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════╗
echo ║     🦞 老六 Chat  一键安装向导          ║
echo ║     让任何电脑都能跑起来的超级 Agent    ║
echo ╚══════════════════════════════════════════╝
echo.
echo  本向导将帮你完成：
echo    1️⃣  检测 / 安装 Python
echo    2️⃣  检测 / 安装 Node.js
echo    3️⃣  安装 OpenClaw 网关
echo    4️⃣  安装 Claude Code CLI
echo    5️⃣  配置 API Key
echo    6️⃣  创建桌面快捷方式
echo.
echo ──────────────────────────────────────────
echo.
pause

:: ====== Step 0: 检查是否已配置过 ======
if exist "blue-mode\config.json" (
    findstr /C:"你的DeepSeek" "blue-mode\config.json" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [✓] 检测到已有配置文件，跳过 API Key 引导
        set HAS_CONFIG=1
    )
)

:: ====== Step 1: Python ======
echo.
echo ═══════════════════════════════════════════
echo  第 1 步：检测 Python
echo ═══════════════════════════════════════════

set PYTHON_OK=0
python --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [✓] %%v 已安装
    set PYTHON_OK=1
) else (
    python3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%v in ('python3 --version 2^>^&1') do echo  [✓] %%v 已安装
        set PYTHON_OK=1
        set PYTHON_CMD=python3
    ) else (
        echo  [✗] Python 未安装
        echo.
        echo  需要 Python 3.10 或以上版本
        echo  正在打开下载页面...
        start https://www.python.org/downloads/
        echo.
        echo  ▸ 请下载并安装 Python（勾选"Add to PATH"）
        echo  ▸ 安装完成后按任意键继续...
        pause >nul
        python --version >nul 2>&1
        if !errorlevel! equ 0 (
            set PYTHON_OK=1
            echo  [✓] Python 安装成功！
        ) else (
            echo  [✗] 仍未检测到 Python，请手动安装后重新运行本脚本
            pause
            exit /b 1
        )
    )
)

if not defined PYTHON_CMD set PYTHON_CMD=python

:: ====== Step 2: pip + Pillow ======
echo.
echo  [安装] 检查 Python 依赖...
%PYTHON_CMD% -m pip install pillow --quiet 2>&1 >nul
if !errorlevel! equ 0 (
    echo  [✓] Pillow (图像处理) 已就绪
) else (
    echo  [⚠] Pillow 安装失败，截图功能可能不可用
)

:: ====== Step 3: Node.js ======
echo.
echo ═══════════════════════════════════════════
echo  第 2 步：检测 Node.js
echo ═══════════════════════════════════════════

set NODE_OK=0
node --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo  [✓] Node.js %%v 已安装
    set NODE_OK=1
) else (
    echo  [✗] Node.js 未安装
    echo.
    echo  需要 Node.js 18 或以上版本
    echo  正在打开下载页面...
    start https://nodejs.org/
    echo.
    echo  ▸ 请下载安装 Node.js LTS 版本
    echo  ▸ 安装完成后按任意键继续...
    pause >nul
    node --version >nul 2>&1
    if !errorlevel! equ 0 (
        set NODE_OK=1
        echo  [✓] Node.js 安装成功！
    ) else (
        echo  [✗] 仍未检测到 Node.js，请手动安装后重新运行本脚本
        pause
        exit /b 1
    )
)

:: ====== Step 4: npm 依赖 ======
echo.
echo ═══════════════════════════════════════════
echo  第 3 步：安装 OpenClaw 网关
echo ═══════════════════════════════════════════

if exist "node_modules\.bin\openclaw.cmd" (
    echo  [✓] OpenClaw 已安装
) else (
    echo  [安装] 正在安装 OpenClaw（可能需要几分钟）...
    call npm install --quiet 2>&1 >nul
    if !errorlevel! equ 0 (
        echo  [✓] OpenClaw 安装完成
    ) else (
        echo  [✗] 安装失败，请检查网络连接
        echo  你可以稍后手动运行: npm install
    )
)

:: ====== Step 5: Claude Code CLI ======
echo.
echo ═══════════════════════════════════════════
echo  第 4 步：安装 Claude Code CLI
echo ═══════════════════════════════════════════

claude --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('claude --version 2^>^&1') do echo  [✓] Claude Code %%v 已安装
) else (
    echo  [安装] 正在安装 Claude Code CLI（可能需要几分钟）...
    call npm install -g @anthropic-ai/claude-code 2>&1
    if !errorlevel! equ 0 (
        echo  [✓] Claude Code CLI 安装完成
    ) else (
        echo  [⚠] Claude Code CLI 安装失败
        echo  你可以稍后手动运行: npm install -g @anthropic-ai/claude-code
    )
)

:: ====== Step 6: API Key 配置 ======
echo.
echo ═══════════════════════════════════════════
echo  第 5 步：配置 API Key
echo ═══════════════════════════════════════════

if defined HAS_CONFIG (
    echo  [✓] 已有配置，跳过
    goto :shortcut
)

if not exist "blue-mode\config.json" (
    if exist "blue-mode\config.json.template" (
        copy "blue-mode\config.json.template" "blue-mode\config.json" >nul
    )
)

echo.
echo  ┌─────────────────────────────────────────┐
echo  │  需要 DeepSeek API Key 才能使用 AI 功能 │
echo  │                                         │
echo  │  申请地址: https://platform.deepseek.com │
echo  │  新用户注册即送额度，无需绑定支付方式   │
echo  │                                         │
echo  │  获得 Key 后粘贴到这里（sk-开头）       │
echo  └─────────────────────────────────────────┘
echo.
set /p API_KEY="▸ 请输入 API Key: "

if "!API_KEY!"=="" (
    echo  [⚠] 未输入 Key，你可以启动后在侧边栏 ⚙ 设置中填写
) else (
    set /p API_URL="▸ API 地址 (直接回车=官方): "
    if "!API_URL!"=="" set API_URL=https://api.deepseek.com/v1

    echo  [保存] 正在写入配置...
    %PYTHON_CMD% -c "import json, os; p=r'blue-mode\config.json'; c=json.load(open(p,'r',encoding='utf-8')); c.setdefault('deepseek',{})['api_key']='!API_KEY!'; c.setdefault('deepseek',{})['base_url']='!API_URL!'; json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)"
    if exist ".openclaw\openclaw.json" (
        %PYTHON_CMD% -c "import json, os; p=r'.openclaw\openclaw.json'; c=json.load(open(p,'r',encoding='utf-8')); c.setdefault('models',{}).setdefault('providers',{}).setdefault('deepseek',{})['apiKey']='!API_KEY!'; c['models']['providers']['deepseek']['baseUrl']='!API_URL!'; json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)"
    )
    echo  [✓] API Key 已保存
)

:: ====== Step 7: 桌面快捷方式 ======
:shortcut
echo.
echo ═══════════════════════════════════════════
echo  第 6 步：创建桌面快捷方式
echo ═══════════════════════════════════════════

set DESKTOP=%USERPROFILE%\Desktop
if exist "%USERPROFILE%\OneDrive\Desktop" set DESKTOP=%USERPROFILE%\OneDrive\Desktop

set SHORTCUT=%DESKTOP%\老六Chat.lnk
set LAUNCHER=%~dp0老六一键启动.bat

powershell.exe -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%LAUNCHER%'; $s.WorkingDirectory = '%~dp0'; $s.Description = '老六 Chat - AI 桌面助手'; $s.Save()" 2>nul

if exist "%SHORTCUT%" (
    echo  [✓] 桌面快捷方式已创建: 老六Chat
) else (
    echo  [⚠] 快捷方式创建失败（不影响使用，可手动创建）
    echo  右键 老六一键启动.bat → 发送到桌面快捷方式
)

:: ====== 完成 ======
echo.
echo ╔══════════════════════════════════════════╗
echo ║         ✅ 安装完成！                   ║
echo ╚══════════════════════════════════════════╝
echo.
echo  🦞 启动方式：
echo     ▸ 桌面双击 "老六Chat" 快捷方式
echo     ▸ 或双击 "老六一键启动.bat"
echo.
echo  📖 使用提示：
echo     ▸ 打开后自动启动网关 + 聊天面板
echo     ▸ 红色模式 = AI对话  |  蓝色模式 = 编程执行
echo     ▸ 侧边栏 ⚙ 可随时修改模型和 Key
echo     ▸ 📎 按钮可上传图片/文件给 AI 分析
echo     ▸ 聊天框输入 /config 查看当前配置
echo.
echo  按任意键启动老六 Chat...
pause >nul

:: 启动
start "" "%~dp0老六一键启动.bat"
exit
