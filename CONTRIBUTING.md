# 贡献指南

感谢你对老六 Chat 的关注！欢迎参与贡献代码、报告问题或提供建议。

## 行为准则

- 尊重所有贡献者，保持友好和建设性的讨论
- 不提交恶意代码、后门或侵犯他人隐私的功能
- 不提交包含 API 密钥、密码等敏感信息的代码

## 如何贡献

### 报告 Bug

1. 在 [GitHub Issues](../../issues) 中创建新 Issue
2. 使用清晰的标题描述问题
3. 提供以下信息：
   - 操作系统和版本（如 Windows 11 23H2）
   - Python 版本（`python --version`）
   - Node.js 版本（`node --version`）
   - 复现步骤
   - 期望行为 vs 实际行为
   - 相关截图（注意打码敏感信息！）

### 提交代码

1. **Fork** 本仓库
2. 创建功能分支：`git checkout -b feature/你的功能名`
3. 进行修改并测试
4. 确保 **不要** 提交以下文件：
   - `blue-mode/config.json`（包含 API 密钥）
   - `chat-data/`（聊天记录）
   - 任何包含个人信息的文件
5. 提交代码：`git commit -m "feat: 添加了某某功能"`
6. 推送到你的仓库：`git push origin feature/你的功能名`
7. 创建 **Pull Request**

### Commit 规范

建议使用以下前缀：
- `feat:` — 新功能
- `fix:` — Bug 修复
- `docs:` — 文档更新
- `style:` — 代码格式调整
- `refactor:` — 重构
- `perf:` — 性能优化
- `chore:` — 构建/工具链变更

### 代码风格

- Python 代码：遵循 PEP 8
- 使用有意义的变量名和注释
- UI 相关修改请同时适配红色和蓝色主题

## 开发环境

1. Python 3.10+
2. Node.js 18+
3. 克隆仓库后运行 `setup.bat` 安装依赖
4. 将 `blue-mode/config.json.template` 复制为 `blue-mode/config.json` 并填入你的 API Key

## ⚠️ 重要提醒

- **绝对不要** 在 PR 中包含 `blue-mode/config.json`
- **绝对不要** 在代码中硬编码 API Key
- 聊天数据、截图等个人文件已由 `.gitignore` 排除
- 如有疑问，先创建 Issue 讨论再开始编码
