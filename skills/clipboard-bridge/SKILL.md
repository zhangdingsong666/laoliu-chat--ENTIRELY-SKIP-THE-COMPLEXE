---
name: clipboard-bridge
description: 读写 Windows 剪贴板。让 agent 能读取你复制的内容，或将结果写入剪贴板供你粘贴。
metadata:
  openclaw:
    requires: { os: ["win32"] }
---

# Clipboard Bridge — 剪贴板管道

直接读写 Windows 剪贴板，实现「复制一段文字 → agent 自动处理 → 结果写回剪贴板」的流畅工作流。

## 读取剪贴板

```powershell
powershell -File "{baseDir}/scripts/clip-read.ps1"
```

返回当前剪贴板中的文本内容。

## 写入剪贴板

```powershell
powershell -File "{baseDir}/scripts/clip-write.ps1" -Text "要写入的内容"
```

## 典型使用场景

### 场景1：翻译
用户复制一段英文 → agent 读剪贴板 → 翻译成中文 → 写回剪贴板
```
1. 用户说："翻译我复制的"
2. 你执行 clip-read.ps1 获取文本
3. 翻译
4. 执行 clip-write.ps1 写回翻译结果
5. 告诉用户："已翻译并放回剪贴板，直接粘贴即可"
```

### 场景2：格式化
用户复制 JSON → agent 读剪贴板 → 格式化 → 写回

### 场景3：提取信息
用户复制网页内容 → agent 提取关键信息 → 写回摘要

## 注意

- `Get-Clipboard` 只能读取文本。图片/文件剪贴板内容无法通过此方法读取。
- 剪贴板是系统共享资源，读写之间可能有其他程序修改。
