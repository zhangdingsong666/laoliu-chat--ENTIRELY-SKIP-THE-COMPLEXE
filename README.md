<p align="center">
  <img src="app-icon.ico" width="96" height="96" alt="老六 Chat 图标">
</p>

<h1 align="center">🦞 老六 Chat — AI 桌面超级 Agent</h1>

<p align="center">
  <strong>一个开箱即用的双模式 AI 桌面助手</strong><br>
  🔴 红色模式：AI 智能对话 · 🔵 蓝色模式：直连 Claude Code 编程执行
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Node.js-18+-green?logo=node.js&logoColor=white" alt="Node.js">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT%20Custom-red" alt="License">
  <img src="https://img.shields.io/badge/Version-1.0.0-brightgreen" alt="Version">
</p>

---

## ⚠️ 使用前必读

> **本软件调用 AI API 可能产生费用，使用者自行承担。**
> API Key 是敏感信息，请勿分享给他人。聊天记录和截图均存储在本地，不会上传到作者服务器。

---

## 📥 快速安装

### 方式一：下载发行版（推荐）

> 🔗 **[→ 点击这里下载最新版本](../../releases/latest)**

1. 下载 `老六Chat-v1.0.0.zip`
2. 解压到任意目录（建议 `D:\老六Chat`）
3. 双击 `setup.bat`，按提示完成安装
4. 桌面出现快捷方式后，双击启动！

### 方式二：从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/SHIREN9527/laoliu-chat.git
cd laoliu-chat

# 2. 运行安装脚本
setup.bat

# 3. 配置 API Key（见下方说明）
```

### 首次配置 API Key

1. 打开 [DeepSeek 平台](https://platform.deepseek.com) 注册账号并复制 API Key（sk- 开头）
2. 启动老六 Chat 后，点击左侧 ⚙ **设置 API** 按钮
3. 粘贴你的 DeepSeek API Key
4. 点击 💾 保存，状态灯变绿即为连接成功！

> 💡 **提示**：也可以设置环境变量 `DEEPSEEK_API_KEY`，软件会自动读取，无需写入文件。

---

## ✨ 功能特性

### 🔴 红色模式 — AI 智能对话

> 基于 OpenClaw 网关 + DeepSeek 大模型

| 功能 | 说明 |
|------|------|
| 💬 多轮对话 | 上下文记忆，自动携带最近 8 轮对话历史 |
| 📝 历史会话 | SQLite 持久化存储，永久保留，支持重命名/删除 |
| 🎨 Markdown 渲染 | 支持粗体、代码块、链接等完整 Markdown |
| 🔄 模型切换 | 点击或 `/model` 命令一键切换多种模型 |
| ⚡ 斜杠命令 | `/model` `/apikey` `/api` `/config` `/settings` 快速配置 |

### 🔵 蓝色模式（跳跳）— 编程执行

> 直连 Claude Code CLI，无弹窗、无黑框

| 功能 | 说明 |
|------|------|
| 🤖 代码生成 | 写代码、修 Bug、重构，Claude 直接帮你改 |
| 📂 文件操作 | 创建、编辑、删除文件，组织项目结构 |
| 🔧 自动化 | 批量处理、脚本编写、部署流程 |
| 🌐 搜索问答 | 结合联网搜索的智能问答 |
| 🀄 UTF-8 全支持 | 中文输入输出完美适配，不乱码 |

### 📎 文件 / 图片理解

| 方式 | 说明 |
|------|------|
| 🖱 拖放 | 从文件管理器直接拖到输入栏 |
| 📎 按钮 | 点击 📎 选择文件 |
| 📋 粘贴 | Ctrl+V 粘贴剪贴板中的截图 |
| 🖼 图片 | PNG / JPG / GIF / BMP / WebP → AI 视觉分析 |
| 📄 文档 | TXT / PY / MD / JSON / CSV / PDF → AI 文本理解 |

### 📷 屏幕视觉分析

- 点击 **📷** 按钮，自动截图并分析
- 🔴 红模式：AI 描述屏幕上的窗口、图标、内容
- 🔵 蓝模式：识别可交互元素，自动执行操作任务
- 支持 Ollama 本地视觉模型（可选，离线可用）

### ⚙ 灵活配置

- **侧边栏内联设置**：点 ⚙ 展开，实时改 API 地址 / Key / 模型
- **一键同步**：改一个输入框，自动同步所有配置文件
- **环境变量**：支持 `DEEPSEEK_API_KEY` 环境变量，Key 不写文件更安全
- **完整设置窗口**：点"更多"按钮，配置 DeepSeek + Ollama 全部参数

### 🎨 双主题切换

| 主题 | 风格 | 特点 |
|------|------|------|
| 🔴 红色（老六） | 沉稳暗红 | 适合长时间办公，护眼 |
| 🔵 蓝色（跳跳） | 科技亮蓝 | 清爽现代，编程模式首选 |

侧边栏一键切换，豆包风格圆角输入栏，圆形发送按钮。

### 🔒 隐私安全

- ✅ API Key 优先读环境变量，不强制写文件
- ✅ 聊天记录纯本地 SQLite 存储
- ✅ 截图仅在本地临时存储
- ✅ 开源代码，安全可审计
- ✅ `.gitignore` 已排除所有敏感文件

---

## 📖 使用指南

### 基本操作

| 操作 | 方式 |
|------|------|
| 发送消息 | 输入文字后按 **Enter** |
| 换行 | **Shift + Enter** |
| 清屏 | 点击侧边栏 🗑️ 清屏 |
| 聚焦输入框 | 按 **Esc** |
| 切换主对话 | 点击侧边栏 ⭐ 主对话 |

### 切换红/蓝模式

- 点击侧边栏 **🔵 切换跳跳** / **🔴 切换老六** 按钮
- 或在聊天框输入密令 `开启00蓝色模式`

### 上传文件/图片

1. **拖放**：从文件夹拖文件到输入栏
2. **📎 按钮**：点击选择文件
3. **Ctrl+V**：截图后直接粘贴
4. 附件标签出现在输入栏上方，点击 × 可移除

### 截图分析

1. 点击 **📷** 按钮
2. 等待 AI 分析完成
3. 🔴 红模式：AI 描述屏幕上的窗口和内容
4. 🔵 蓝模式：AI 识别可交互元素并自动执行任务

### 斜杠命令

| 命令 | 作用 | 示例 |
|------|------|------|
| `/model <名称>` | 切换模型 | `/model deepseek-v4-pro` |
| `/apikey <密钥>` | 设置 API Key | `/apikey sk-xxxxxxxx` |
| `/api <地址>` | 设置 API 地址 | `/api https://api.deepseek.com/v1` |
| `/config` | 查看当前配置（Key 已脱敏） | `/config` |
| `/settings` | 打开完整设置窗口 | `/settings` |

### 历史会话

- 点击侧边栏 **＋ 新建会话** 创建新对话
- 右键点击历史会话 → **重命名** / **删除**
- 主对话（⭐）每 4 天自动清理
- 历史会话（💬）永久保留

---

## 🏗 技术架构

```
老六 Chat
├── 老六Chat.pyw              # 主程序（Tkinter GUI）
├── 老六Chat.bat              # 启动脚本
├── blue-mode/                # 🔵 蓝色模式引擎
│   ├── zhixin.py             #   知新管道：语义理解 → 视觉定位 → 执行
│   ├── claude_bridge.py      #   Claude Code CLI 桥接器
│   ├── executor.py           #   桌面操控执行器（鼠标/键盘）
│   ├── wengu.py              #   温故调度器（定时提醒）
│   ├── themes.py             #   双主题配色定义
│   └── config.json.template  #   配置模板（复制为 config.json 使用）
├── skills/                   # OpenClaw 技能模块
│   ├── desktop-control/      #   鼠标键盘操控
│   ├── screen-insight/       #   截图+视觉分析
│   ├── clipboard-bridge/     #   剪贴板读写
│   └── ...                   #   更多技能
└── package.json              # Node.js 依赖声明
```

### 数据流

```
🔴 红色模式（对话）：
用户输入 → OpenClaw 网关 → DeepSeek API → 回复 → GUI 渲染

🔵 蓝色模式（执行）：
用户输入 → zhixin.run() → claude_bridge.py → Claude Code CLI → 结果 → GUI 渲染

📎 文件处理：
附件 → base64 编码（图片）/ 文本拼接（文档） → 拼接为 prompt → 发送给 AI
```

---

## ⚠️ 重要声明

### 📜 开源协议

本项目采用 **定制 MIT 协议**，完整协议见 [LICENSE](LICENSE)：

- ✅ 个人学习、研究、非商业用途自由使用
- ✅ 二次开发欢迎，但需在源码中标注改动内容和时间
- ❌ **严禁** 用于任何商业盈利目的
- ❌ **严禁** 未授权转载 / 打包分发
- ⚠️ 转载 / 二次分发 **必须联系作者授权**
- ⚠️ 必须保留原作者署名 **SHIREN9527** 和本协议全文

### 🔐 安全警告

> **请认真阅读以下内容：**

- ⚠️ 本软件调用 AI API 可能产生 **费用**，使用者自行承担所有费用
- ⚠️ API Key 是敏感信息，**请勿分享给他人**，泄露可能导致财产损失
- ⚠️ 蓝色模式使用 `--dangerously-skip-permissions` 参数，Claude Code 可无弹窗操作文件
- ⚠️ 请勿将本软件用于任何 **非法用途**，使用者对自身行为负全部责任
- ⚠️ 建议在 **虚拟机** 或测试环境中首次运行蓝色模式

### 🛡 隐私提醒

- 📂 聊天记录本地存储在 `chat-data/` 文件夹（SQLite 数据库）
- 📸 截图临时存储在 `blue-mode/screenshots/` 目录
- ☁️ 发送文件/图片给 AI 意味着内容会 **传输到 API 服务商**（DeepSeek / Anthropic）
- 🔒 敏感信息请勿通过本软件传输
- 🗑️ 发布到 GitHub 前已排除所有配置文件、聊天记录、截图

### 💰 费用参考

| 模型 | 输入价格 | 输出价格 |
|------|----------|----------|
| DeepSeek V4 Flash | ¥1.00 / 百万 token | ¥4.00 / 百万 token |
| DeepSeek V4 Pro | ¥2.00 / 百万 token | ¥8.00 / 百万 token |
| DeepSeek Chat (V3) | ¥1.00 / 百万 token | ¥2.00 / 百万 token |

> 普通对话每次约消耗 1000-3000 token，费用极低。请自行关注 [DeepSeek 平台](https://platform.deepseek.com) 余额。

---

## 🔧 常见问题

<details>
<summary><strong>Q: 启动后状态灯显示红色"无连接"？</strong></summary>

请检查：
1. 是否已填入正确的 API Key
2. API 地址是否正确（默认 `https://api.deepseek.com/v1`）
3. 网络是否能访问 DeepSeek API
4. 点击 ⚙ 设置 API → 保存后重启软件
</details>

<details>
<summary><strong>Q: 蓝色模式无法使用？</strong></summary>

蓝色模式需要安装 Claude Code CLI：
```bash
npm install -g @anthropic-ai/claude-code
```
安装后重启老六 Chat 即可。
</details>

<details>
<summary><strong>Q: 📷 截图功能无响应？</strong></summary>

需要安装 Ollama 并下载视觉模型：
```bash
# 安装 Ollama: https://ollama.com
ollama pull minicpm-v:8b
```
</details>

<details>
<summary><strong>Q: 如何备份聊天记录？</strong></summary>

复制 `chat-data/sessions.db` 文件即可。所有对话历史都在这个 SQLite 数据库中。
</details>

<details>
<summary><strong>Q: 拖放文件不生效？</strong></summary>

点击 📎 按钮手动选择文件作为备选方案。部分系统可能因权限问题限制了拖放。
</details>

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

**提交前请务必确认：**
- ❌ 不要提交 `blue-mode/config.json`（含 API Key）
- ❌ 不要提交 `chat-data/` 中的任何文件
- ✅ 已在 `.gitignore` 中排除了上述敏感文件

---

## 👤 作者

**SHIREN9527**

- 📮 问题反馈：[GitHub Issues](../../issues)
- 📜 完整更新日志：[CHANGELOG.md](CHANGELOG.md)

---

<p align="center">
  <sub>🦞 Made with ❤️ by SHIREN9527 | © 2026</sub>
</p>
