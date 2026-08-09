---
name: desktop-control
description: 操控鼠标移动点击、键盘输入、窗口管理。让 agent 能像人一样操作桌面应用。
metadata:
  openclaw:
    requires: { os: ["win32"] }
---

# Desktop Control — 桌面操控

控制 Windows 桌面的鼠标、键盘和窗口。

<Warning>
桌面操控是高权限操作。每次执行前确认用户意图明确。不要在没有用户许可的情况下操控鼠标键盘。
</Warning>

## 工具脚本

所有脚本位于 `{baseDir}/scripts/`。

### 鼠标操作

```powershell
# 获取当前鼠标位置
powershell -File "{baseDir}/scripts/click.ps1" -Action getpos

# 移动鼠标到指定坐标 (x, y)
powershell -File "{baseDir}/scripts/click.ps1" -Action move -X 500 -Y 300

# 左键单击
powershell -File "{baseDir}/scripts/click.ps1" -Action click

# 左键双击
powershell -File "{baseDir}/scripts/click.ps1" -Action doubleclick

# 右键单击
powershell -File "{baseDir}/scripts/click.ps1" -Action rightclick

# 拖拽从当前位置到目标位置
powershell -File "{baseDir}/scripts/click.ps1" -Action drag -X 800 -Y 400
```

### 键盘输入

```powershell
# 输入文本（支持中文）
powershell -File "{baseDir}/scripts/type.ps1" -Text "要输入的文字"

# 按下组合键
powershell -File "{baseDir}/scripts/type.ps1" -Keys "^c"     # Ctrl+C
powershell -File "{baseDir}/scripts/type.ps1" -Keys "^v"     # Ctrl+V
powershell -File "{baseDir}/scripts/type.ps1" -Keys "%{TAB}" # Alt+Tab
powershell -File "{baseDir}/scripts/type.ps1" -Keys "#d"     # Win+D

# 按下单个键
powershell -File "{baseDir}/scripts/type.ps1" -Keys "{ENTER}"
powershell -File "{baseDir}/scripts/type.ps1" -Keys "{ESC}"
powershell -File "{baseDir}/scripts/type.ps1" -Keys "{TAB}"
```

SendKeys 特殊符号对照：
- `^` = Ctrl, `%` = Alt, `+` = Shift, `#` = Win
- `{ENTER}`, `{TAB}`, `{ESC}`, `{BACKSPACE}`, `{DELETE}`
- `{F1}` ~ `{F12}`, `{PRTSC}`, `{HOME}`, `{END}`

### 窗口管理

```powershell
# 列出所有可见窗口
powershell -File "{baseDir}/scripts/window.ps1" -Action list

# 搜索包含关键词的窗口
powershell -File "{baseDir}/scripts/window.ps1" -Action find -Title "记事本"

# 激活/前置窗口
powershell -File "{baseDir}/scripts/window.ps1" -Action focus -Title "Chrome"

# 最小化/最大化窗口
powershell -File "{baseDir}/scripts/window.ps1" -Action minimize -Title "微信"
powershell -File "{baseDir}/scripts/window.ps1" -Action maximize -Title "Visual Studio Code"
```

## Python 备选方案

如果 PowerShell 脚本不够用，可以通过 Python pyautogui 实现更精确的控制：

```powershell
# 确保先设置 PYTHONPATH
$env:PYTHONPATH = "D:\龙虾\python-libs"
python -c "import pyautogui; pyautogui.moveTo(500, 300, duration=0.5); pyautogui.click()"
```

## 安全注意事项

1. 在用户活跃的显示器上操作时，移动速度要慢一些（duration 参数）
2. 操作前先截图确认当前屏幕状态
3. 组合使用 screen-insight 确认操作结果
4. 不要在用户正在打字时抢占键盘焦点
