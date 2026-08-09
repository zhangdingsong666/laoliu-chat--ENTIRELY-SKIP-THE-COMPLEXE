---
name: standing-orders
description: 管理常驻命令和定时任务，让 agent 拥有自主执行能力。支持创建 cron 定时任务、心跳巡检项、和管理 agent 的永续操作权限。
metadata:
  openclaw:
    requires: { config: ["gateway.mode"] }
    os: ["win32"]
---

# Standing Orders — 常驻命令系统

你是一个拥有自主执行权的 agent。不需要等待用户每一条指令——你应该在明确的边界内主动行动。

## 三种自主执行机制

| 机制 | 用途 | 持久性 |
|------|------|--------|
| **Standing Orders** (AGENTS.md) | 定义永久权限和例行任务 | 每次会话自动加载 |
| **Cron Jobs** | 精确时间触发的任务 | 跨 Gateway 重启持久 |
| **Heartbeat** | 定期轮询检查（~30分钟） | 由 HEARTBEAT.md 控制 |

## 如何创建 Cron 定时任务

使用 `exec` 工具运行以下命令：

### 一次性提醒
```powershell
openclaw cron create "2026-08-08T18:00:00+08:00" `
  --name "提醒-开会" `
  --session main `
  --system-event "提醒用户：18:00 有会议" `
  --wake now `
  --delete-after-run
```

### 周期性任务
```powershell
# 每天上午9点执行
openclaw cron create `
  --name "每日站会提醒" `
  --cron "0 9 * * 1-5" `
  --tz Asia/Shanghai `
  --session main `
  --system-event "检查今天的日历和待办事项，生成摘要"

# 每小时检查 C 盘空间
openclaw cron create `
  --name "C盘空间监控" `
  --cron "0 * * * *" `
  --tz Asia/Shanghai `
  --session main `
  --system-event "检查C盘剩余空间，如果低于5GB就提醒用户"
```

### 查看和管理任务
```powershell
openclaw cron list
openclaw cron get <job-id>
openclaw cron delete <job-id>
```

## 心跳巡检（Heartbeat）

心跳每约30分钟自动触发一次。在 `HEARTBEAT.md` 中配置巡检项。

当前心跳配置位置：`D:\龙虾\HEARTBEAT.md`

## 安全边界

- ✅ 可以：检查状态、生成报告、整理文件、提醒用户
- ⚠️ 需要确认：发送外部消息、修改系统配置、删除文件
- ❌ 禁止：自动充值、泄露隐私、破坏性操作

## 当前激活的常驻命令

参见 `AGENTS.md` 中的 `## Standing Orders` 章节。
