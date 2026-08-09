---
name: chat-app
description: 老六的独立桌面聊天窗口。双击 D:\龙虾\老六Chat.bat 即可打开，不需要浏览器和终端。
metadata:
  openclaw:
    requires: { bins: ["python"], os: ["win32"] }
---

# 老六 Chat - 桌面聊天窗口

一个独立的桌面聊天窗口，双击 `D:\龙虾\老六Chat.bat` 即可启动。

## 特性

- 🖥️ 独立窗口，不需要浏览器和终端
- 🖼️ **内嵌图片显示** — 截图、生成的图片直接在聊天中显示
- 📷 **一键截图** — 工具栏按钮快速截屏
- 🎨 Catppuccin Mocha 暗色主题
- ⌨️ Ctrl+Enter 发送，Shift+Enter 换行
- 📝 Markdown 渲染（粗体、代码块高亮）
- 🔗 自动检测链接和图片路径
- 🔴 实时状态灯（绿色=就绪，黄色=处理中，红色=离线）
- ⏱️ 显示响应耗时

## 前置条件

1. openclaw gateway 必须正在运行。先启动 gateway：

```powershell
# 双击 Start-OpenClaw.bat
# 或命令行
D:\龙虾\Start-OpenClaw.ps1
```

2. Python 需安装 Pillow 以支持图片内嵌显示：

```powershell
pip install --target D:\龙虾\python-libs Pillow
```

## 启动方式

- 双击 `D:\龙虾\老六Chat.bat`
- 或命令行：`pythonw.exe D:\龙虾\老六Chat.pyw`

## 如何在桌面创建快捷方式

右键 `D:\龙虾\老六Chat.bat` → 发送到 → 桌面快捷方式。

## 图片功能

- Agent 回复中的图片路径（如截图）会自动显示
- 点击 📷 按钮快速截全屏
- 截图保存在 `D:\龙虾\screenshots\` 目录
- 支持 PNG、JPG、GIF、BMP、WebP 格式

## 技术架构

- 前端：Python tkinter + Pillow
- 后端：通过 `openclaw agent` CLI 调用 DeepSeek V4 Flash
- 通信：子进程 + 队列（非阻塞 UI）
