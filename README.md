# TrendRadar

TrendRadar 是一个“每日热点灵感雷达”系统。它不是新闻聚合器，不是优增关键词筛选器，也不是专业报告筛选器。

系统核心目标是从中国主流热点平台中，优先发现当天最热门、最有话题感、最容易引发讨论、最能带来灵感的内容，再判断是否能与保险优增、人力推动、职业选择、成长转型、女性成长、家庭责任、健康养老、财富风险、平台价值、圈层社交、活动经营、AI 时代变化等产生轻度连接。

## 核心原则

核心排序权重：

- 热点性：45%
- 趣味性/话题性：35%
- 弱关联性：15%
- 安全性：5%

核心原则：

热点性 > 趣味性/话题性 > 弱关联性。

TrendRadar 不会按“保险、优增、职业”等关键词提前过滤热点。系统先看当天热点本身是否足够热、足够有讨论感，再判断是否存在轻度连接和灵感价值。

## 目录结构

```text
TrendRadar/
├── .github/
│   └── workflows/
├── config/
│   ├── sources.json
│   ├── scoring.json
│   ├── ai_prompt.md
│   └── schedule.md
├── scripts/
│   ├── fetch_hotspots.py
│   ├── health_check.py
│   ├── merge_clusters.py
│   ├── analyze_inspiration.py
│   ├── build_pages.py
│   └── archive_daily.py
├── data/
│   ├── snapshots/
│   ├── health/
│   ├── clusters/
│   ├── daily/
│   └── library/
├── output/
│   ├── today.md
│   ├── today.html
│   └── archive/
├── docs/
│   └── index.html
├── requirements.txt
├── README.md
└── .gitignore
```

## 自动化计划

本阶段不创建 GitHub Actions workflow，只记录未来云端自动化时间安排。

所有日期、文件名和页面显示时间必须使用 `Asia/Shanghai`。

热点抓取计划：

- 北京时间每日 08:00、10:00、12:00、14:00、16:00、18:00、20:00、22:00
- GitHub Actions UTC cron：`0 0-14/2 * * *`

AI 灵感分析计划：

- 北京时间每日 08:30、12:30、18:30、22:30
- GitHub Actions UTC cron：`30 0,4,10,14 * * *`

每日归档计划：

- 北京时间每日 23:30
- GitHub Actions UTC cron：`30 15 * * *`

## 脚本职责

- `scripts/fetch_hotspots.py`：负责抓取热点并保存 `data/snapshots/YYYY-MM-DD/HHMM.json`
- `scripts/health_check.py`：负责生成信息源健康状态 `data/health/YYYY-MM-DD_HHMM.json`
- `scripts/merge_clusters.py`：负责把当天多个快照合并为热点簇 `data/clusters/YYYY-MM-DD.json`
- `scripts/analyze_inspiration.py`：负责根据热点簇生成 AI 灵感分析 `data/daily/YYYY-MM-DD_analysis.json`
- `scripts/build_pages.py`：负责生成 `output/today.md`、`output/today.html`、`docs/index.html`
- `scripts/archive_daily.py`：负责生成每日归档 `data/daily/YYYY-MM-DD_final.json` 和 `output/archive/YYYY-MM-DD.html`

## 第一阶段状态

项目骨架已创建，尚未接入真实抓取和 AI。

当前只包含：

- 信息源占位配置
- 评分权重配置
- AI 分析定位说明
- 自动化时间安排说明
- 可直接运行的 Python 占位脚本
- 今日输出和 GitHub Pages 占位页面

本阶段没有写入任何 API Key，也没有创建 GitHub Actions workflow。
