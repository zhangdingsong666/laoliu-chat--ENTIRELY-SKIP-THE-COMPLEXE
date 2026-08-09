---
name: screen-insight
description: 截取 Windows 屏幕并分析内容。支持全屏、区域、活动窗口截图。截图后调用视觉模型分析画面。
metadata:
  openclaw:
    requires: { os: ["win32"] }
---

# Screen Insight — 屏幕可视化

截取屏幕画面并进行视觉分析。让你「看见」用户的屏幕。

## 截图

所有脚本位于 `{baseDir}/scripts/`。

```powershell
# 全屏截图（保存到 D:\龙虾\screenshots\）
powershell -File "{baseDir}/scripts/capture.ps1" -Mode full

# 截取主显示器
powershell -File "{baseDir}/scripts/capture.ps1" -Mode screen -Index 0

# 区域截图
powershell -File "{baseDir}/scripts/capture.ps1" -Mode region -X 100 -Y 100 -Width 500 -Height 300

# 截取活动窗口
powershell -File "{baseDir}/scripts/capture.ps1" -Mode window
```

## 分析截图

截图保存为 PNG 文件后，使用你的 vision 能力分析画面内容：

1. 执行截图脚本 → 获得文件路径
2. 读取图片文件
3. 描述图片中看到的内容：窗口标题、文字内容、UI 元素位置等

## 典型使用场景

### 场景1：帮用户看屏幕
```
用户："看看我在做什么"
→ 全屏截图 → 分析 → 描述当前屏幕状态
```

### 场景2：辅助操作验证
```
配合 desktop-control 使用：
1. 点击某个按钮 → 截图 → 确认按钮是否被按下
2. 切换窗口 → 截图 → 确认是否切到了正确的窗口
```

### 场景3：错误诊断
```
用户："帮我看看这个报错"
→ 截取活动窗口 → 读取错误信息 → 给出解决方案
```

## 截图保存位置

所有截图保存在 `D:\龙虾\screenshots\` 目录下，文件名格式：`screenshot-YYYYMMDD-HHmmss.png`
