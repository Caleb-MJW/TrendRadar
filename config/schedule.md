# TrendRadar 云端自动化时间安排

所有日期、文件名和页面显示时间必须使用 `Asia/Shanghai`。

## 热点抓取

北京时间每日：

- 08:00
- 10:00
- 12:00
- 14:00
- 16:00
- 18:00
- 20:00
- 22:00

GitHub Actions UTC cron：

```cron
0 0-14/2 * * *
```

## AI 灵感分析

北京时间每日：

- 08:30
- 12:30
- 18:30
- 22:30

GitHub Actions UTC cron：

```cron
30 0,4,10,14 * * *
```

## 每日归档

北京时间每日：

- 23:30

GitHub Actions UTC cron：

```cron
30 15 * * *
```
