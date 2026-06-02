# TrendRadar

TrendRadar 是一个“每日热点灵感雷达”系统。它不是新闻聚合器，不是优增关键词筛选器，也不是专业报告筛选器。

系统核心目标是从中国主流热点平台中，优先发现当天最热门、最有话题感、最容易引发讨论、最能带来灵感的内容，再判断是否能与保险优增、人力推动、职业选择、成长转型、女性成长、家庭责任、健康养老、财富风险、平台价值、圈层社交、活动经营、AI 时代变化等产生轻度连接。

## 核心原则

TrendRadar 的数据来源必须是各平台真实热门榜单中的原始内容，而不是关键词搜索结果。

正确流程：

1. 先抓取平台热门榜单：微博热搜榜、百度热搜榜、抖音热点榜、小红书热榜、今日头条热榜、腾讯热点、知乎热榜、B站热门。
2. 保存热榜原始内容：来源平台、榜单名称、原标题、原平台排名、热度值、抓取时间、原文链接、榜单条目链接、榜单页面链接。
3. 再从已抓取的真实热榜内容中判断：是否热门、是否有趣、是否有话题感、是否能与用户工作产生弱关联。
4. 严禁反向使用“增员、保险、职业、成长、女性”等关键词去平台搜索，再把搜索结果当成热点素材。

数据源 = 平台真实热门榜单。

平台搜索不是数据来源。`search_url` 只允许作为后台人工辅助复查字段，不属于正式来源，不参与 `source_level`，也不作为页面主溯源按钮展示。

AI 分析 = 只能分析已抓取的热榜内容，不能决定抓取关键词。

核心排序权重：

- 热点性：45%
- 趣味性/话题性：35%
- 弱关联性：15%
- 安全性：5%

核心原则：

热点性 > 趣味性/话题性 > 弱关联性。

TrendRadar 不会按“保险、优增、职业”等关键词提前过滤热点。系统先看当天热点本身是否足够热、足够有讨论感，再判断是否存在轻度连接和灵感价值。

## 来源字段与溯源规则

正式出处优先级：

1. `source_url`：原文、原视频、原笔记链接。
2. `board_item_url`：平台热榜条目链接。
3. `board_url`：平台热榜页面链接。
4. `search_url`：人工辅助复查链接，不属于正式来源，不在主页面卡片中展示。

来源等级字段 `source_level` 只允许：

- `original`
- `board_item`
- `board_page`
- `no_link`

页面展示必须区分：

- 正式来源：查看原文、查看榜单条目、查看热榜页面。

如果没有 `source_url`、`board_item_url`、`board_url`，页面必须显示“暂无正式出处，不进入素材参考”。

真实素材必须来自平台热榜、榜单条目、原文链接或热榜页面。真实模式下，只有 `source_origin_type = hotlist` 且 `is_reference_valid = true` 的内容，才可以进入正式素材分析和素材库建议。若 `source_origin_type = keyword_search`，必须直接丢弃，不能进入分析。

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
