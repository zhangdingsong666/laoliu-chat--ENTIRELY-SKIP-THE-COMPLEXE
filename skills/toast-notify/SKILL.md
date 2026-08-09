---
name: toast-notify
description: 发送 Windows 系统通知。任务完成、需要决策、状态更新时弹 toast 提醒用户。
metadata:
  openclaw:
    requires: { os: ["win32"] }
---

# Toast Notify — Windows 系统通知

发送 Windows 10/11 原生 toast 通知。让你能主动提醒用户，而不是被动等待用户查看。

## 发送通知

```powershell
# 基本通知
powershell -File "{baseDir}/scripts/notify.ps1" -Title "任务完成" -Message "文件已下载到 D:\龙虾\"

# 带图标的通知
powershell -File "{baseDir}/scripts/notify.ps1" -Title "⚠️ 警告" -Message "C盘剩余空间不足 5GB"

# 需要操作的通知
powershell -File "{baseDir}/scripts/notify.ps1" -Title "确认操作" -Message "是否删除 30 天前的日志文件？请回复是或否"
```

## 典型使用场景

### 场景1：长任务完成通知
```
用户让你下载一个大文件 → 后台执行 → 完成后弹通知"下载完成"
```

### 场景2：决策请求
```
agent 遇到需要用户决策的情况 → 弹通知说明情况 → 等待用户回复
```

### 场景3：状态提醒
```
C盘监控发现空间不足 → 弹通知 + 给出清理建议
```

### 场景4：定时播报
```
配合 cron：每小时弹一次"当前系统状态正常" 或 "发现N个问题需处理"
```

## 通知策略

- ✅ 任务完成、重要状态变化 → 立即通知
- ⚠️ 常规进度更新 → 合并为每30分钟一次
- ❌ 深夜（23:00-07:00）→ 除非用户明确要求，否则推迟到早上
- ❌ 不要在1分钟内连发超过3条通知
