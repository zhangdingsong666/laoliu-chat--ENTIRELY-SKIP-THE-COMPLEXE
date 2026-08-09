# Screen Monitor Skill

实时截屏并用本地 Ollama 视觉模型分析屏幕内容。

## 依赖
- Ollama 运行在 `http://127.0.0.1:11434`
- 视觉模型: `minicpm-v:8b`（或其他支持图像的模型）
- `screen-insight/capture.ps1` 用于截屏

## 功能

### describe — 描述屏幕
截取全屏 → Ollama 视觉模型分析 → 返回中文描述
```powershell
.\monitor.ps1 -Action describe
.\monitor.ps1 -Action describe -Prompt "这个屏幕上有哪些IDE窗口？"
```

### find — 查找元素
在屏幕上查找指定窗口/按钮/文字 → 返回坐标描述
```powershell
.\monitor.ps1 -Action find -Prompt "开始菜单按钮"
.\monitor.ps1 -Action find -Prompt "Chrome浏览器窗口"
```

### watch — 持续监控
每隔 N 秒截图分析，检测变化
```powershell
.\monitor.ps1 -Action watch -Interval 10 -Count 6
.\monitor.ps1 -Action watch -Prompt "检测是否有新的弹窗" -Interval 5 -Count 20
```

## 使用方式
- 在老六Chat中说 "看看屏幕"、"帮我找XX窗口"、"监控屏幕变化"
- Agent 调用此 skill 的 monitor.ps1 脚本
- 视觉分析结果通过文本返回

## 限制
- 模型运行在本地 CPU，分析需要 10-30 秒
- 首次运行需要加载模型到内存（额外等待）
- 图像通过 base64 传输到 Ollama API
