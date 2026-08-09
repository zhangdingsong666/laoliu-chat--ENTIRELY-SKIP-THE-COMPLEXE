---
name: file-watcher
description: 监控文件夹变化（新增/修改/删除），自动触发处理流程。支持通配符过滤和多种事件类型。
metadata:
  openclaw:
    requires: { os: ["win32"] }
---

# File Watcher — 文件监听

监控指定文件夹的文件变化事件，在有新文件或文件被修改时自动处理。

## 启动监听

```powershell
# 监控文件夹，检测到变化后输出事件信息
powershell -File "{baseDir}/scripts/watch.ps1" -Path "D:\龙虾" -Filter "*.*" -DurationSeconds 30

# 只监控 .csv 文件
powershell -File "{baseDir}/scripts/watch.ps1" -Path "D:\龙虾" -Filter "*.csv" -DurationSeconds 60

# 包含子文件夹
powershell -File "{baseDir}/scripts/watch.ps1" -Path "D:\龙虾" -Filter "*.py" -IncludeSubdirs -DurationSeconds 120
```

## 如何使用

当用户说"帮我盯着某个文件夹"时：

1. 在后台启动 file-watcher 监听目标文件夹（用 exec background 模式）
2. 检测到变化后，根据文件类型自动处理：
   - `.csv` → 分析数据，生成报告
   - `.py` → 检查代码质量
   - `.log` → 查找错误
   - 新图片 → 压缩/分类
3. 处理完通过 toast-notify 提醒用户

## 后台运行示例

```powershell
# 用 exec 的 background 模式在后台监听 10 分钟
exec: {
  command: "powershell -File {baseDir}/scripts/watch.ps1 -Path 'D:\龙虾' -DurationSeconds 600",
  background: true,
  timeout: 660
}
```

## 注意

- 文件监听会持续占用进程，记得设置合理的 DurationSeconds
- 高频变化的文件夹（如日志目录）建议用通配符过滤
- 不要在 C:\Windows 等系统目录上监听
