import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
MODE = "mock"

PLATFORMS = [
    ("微博热搜", "社交热搜"),
    ("百度热搜", "搜索热榜"),
    ("抖音热点", "短视频热点"),
    ("小红书热点", "生活方式"),
    ("今日头条热榜", "资讯热榜"),
    ("腾讯热点", "门户热点"),
    ("知乎热榜", "问答讨论"),
    ("B站热门", "视频热门"),
]

MOCK_TITLES = [
    ("年轻人重新规划职业安全感", ["职业选择", "年轻人", "安全感"]),
    ("AI工具改变职场效率", ["AI时代变化", "职场效率", "工具"]),
    ("热门电视剧引发女性成长讨论", ["女性成长", "影视", "成长转型"]),
    ("健康管理成为家庭新话题", ["健康养老", "家庭责任", "生活方式"]),
    ("低成本社交方式走红", ["圈层社交", "消费观念变化", "社交"]),
    ("年轻人消费观变化", ["消费观念变化", "年轻人", "财富风险"]),
    ("亲子教育焦虑讨论升温", ["家庭责任", "亲子教育", "成长"]),
    ("大湾区城市生活热度上升", ["城市生活变化", "大湾区", "生活"]),
    ("副业学习计划成为通勤新习惯", ["成长转型", "职业选择", "学习"]),
    ("家庭财务安全感被重新讨论", ["财富风险", "家庭责任", "安全感"]),
    ("职场人开始重视长期健康投资", ["健康养老", "人才发展", "职场"]),
    ("本地生活活动带动社区连接", ["活动经营", "城市生活变化", "圈层社交"]),
    ("宝妈重返职场经验引发共鸣", ["宝妈转型", "女性成长", "职业选择"]),
    ("AI简历助手进入毕业季讨论", ["AI时代变化", "人才发展", "职业选择"]),
    ("年轻家庭尝试低预算周末计划", ["家庭责任", "消费观念变化", "城市生活变化"]),
    ("平台型服务提升小团队效率", ["平台价值", "AI时代变化", "人才发展"]),
    ("银发家庭健康陪伴需求上升", ["健康养老", "家庭责任", "城市生活变化"]),
    ("新型社群活动重塑熟人圈层", ["圈层社交", "活动经营", "平台价值"]),
    ("女性创业者分享轻资产转型", ["女性成长", "成长转型", "平台价值"]),
    ("职场新人用AI整理会议纪要", ["AI时代变化", "工作群话题", "职场效率"]),
    ("城市夜校课程再次受到关注", ["城市生活变化", "成长转型", "圈层社交"]),
    ("年轻人把保险当作风险管理工具", ["财富风险", "职业选择", "家庭责任"]),
    ("亲子运动打卡成为家庭仪式", ["家庭责任", "健康养老", "活动经营"]),
    ("短剧内容带动情绪价值讨论", ["女性成长", "短视频选题", "消费观念变化"]),
]


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def make_item(index: int, now: datetime) -> dict:
    platform, category = PLATFORMS[index % len(PLATFORMS)]
    title, tags = MOCK_TITLES[index]
    rank = index % 10 + 1
    slug = f"mock-{now:%Y%m%d}-{index + 1:02d}"
    search_title = title.replace(" ", "+")
    return {
        "id": slug,
        "source_platform": platform,
        "source_category": category,
        "original_title": title,
        "source_rank": rank,
        "hot_score": max(55, 98 - index * 2 + (8 - rank)),
        "crawl_time": now.isoformat(),
        "source_url": f"https://example.com/{platform}/{slug}",
        "trace_url": f"https://example.com/traces/{slug}",
        "search_url": f"https://example.com/search?q={search_title}",
        "is_top10_direct": rank <= 10,
        "tags_raw": tags,
    }


def main() -> None:
    now = shanghai_now()
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H%M")
    output_dir = Path("data") / "snapshots" / date_text
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{time_text}.json"

    payload = {
        "date": date_text,
        "time": time_text,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": MODE,
        "items": [make_item(index, now) for index in range(len(MOCK_TITLES))],
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated mock hotspot snapshot: {output_path}")


if __name__ == "__main__":
    main()
