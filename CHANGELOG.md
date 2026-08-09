# 更新日志

## v1.0.0 (2026-08-09) 🦞 首次发布

### 🔴 红色模式 — AI 智能对话

- 基于 OpenClaw 网关 + DeepSeek 模型的多轮对话
- 上下文记忆，自动保留最近 8 轮对话
- 历史会话持久化存储（SQLite），永久保留
- 主对话每 4 天自动清理
- Markdown 渲染 + 代码块语法高亮
- 斜杠命令一键切换模型（`/model`）
- 侧边栏内联设置面板（API 地址 / Key / 模型）
- 完整的设置窗口（含 Ollama 配置）

### 🔵 蓝色模式（跳跳）— 编程执行

- 直连 Claude Code CLI，支持编程、代码生成、文件操作
- 知新 (zhixin) 管道：用户指令 → DeepSeek 语义分解 → 执行
- 自动跳过权限弹窗、无黑窗
- 完整 UTF-8 编码支持，中文友好
- 温故 (wengu) 调度器：定时提醒和自动化任务

### 📎 文件 / 图片理解

- 支持拖放文件到输入栏
- 支持点击 📎 按钮选择文件
- 支持 Ctrl+V 粘贴剪贴板图片
- 图片格式：PNG / JPG / GIF / BMP / WebP → AI 视觉分析
- 文档格式：TXT / PY / MD / JSON / CSV / PDF → 文本读取
- 附件标签管理，支持逐个移除

### 📷 屏幕视觉分析

- 📷 按钮一键截图
- 红模式：截图 → Ollama 本地视觉模型分析 → 描述屏幕内容
- 蓝模式：截图 → 知新管道 → 识别可交互元素 → 自动化操作

### ⚙ 灵活配置

- 侧边栏 ⚙ 按钮展开/收起设置面板
- 实时切换 API 地址 / Key / 模型
- 一键同步配置到 config.json + openclaw.json
- 支持环境变量读取 Key（DEEPSEEK_API_KEY）
- 斜杠命令：`/model` `/apikey` `/api` `/config` `/settings`

### 🎨 双主题

- 🔴 红色主题（老六）：沉稳办公风格
- 🔵 蓝色主题（跳跳）：清爽科技风格
- 豆包风格圆角输入栏
- 侧边栏一键切换主题
- 圆形发送按钮 + 状态指示灯

### 🔒 隐私安全

- API Key 支持环境变量，不强制写入文件
- 聊天记录纯本地 SQLite 存储
- 所有隐私相关目录已加入 .gitignore
- 配置模板独立提供（config.json.template）

### 🏗 技术架构

- 前端：Python Tkinter + 自定义主题系统
- AI 引擎：OpenClaw 网关 + DeepSeek API
- 视觉：Ollama 本地多模态模型（minicpm-v）
- 桌面操控：PowerShell + Windows API
- 数据库：SQLite（WAL 模式）

### 📦 环境要求

- Windows 10/11
- Python 3.10+
- Node.js 18+
- （可选）Ollama 本地模型
- （可选）Claude Code CLI
