import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
MODE = "mock"

MATERIAL_USAGE = [
    "朋友圈灵感",
    "工作群话题",
    "短视频选题",
    "早会/会议话题",
    "专业观点素材",
    "观察备用",
    "不建议使用",
]

DIRECTIONS = [
    "职业选择",
    "成长转型",
    "女性成长",
    "宝妈转型",
    "家庭责任",
    "健康养老",
    "财富风险",
    "平台价值",
    "人才发展",
    "圈层社交",
    "活动经营",
    "AI时代变化",
    "城市生活变化",
    "消费观念变化",
    "观察备用",
    "无明显关联",
]

BUCKETS = {
    "top_hot": "全网最热TOP20",
    "top_interesting": "热门有趣TOP20",
    "top_inspiration": "优增灵感TOP15",
    "watchlist": "观察备用",
}

KEYWORD_DIRECTIONS = {
    "职业": "职业选择",
    "AI": "AI时代变化",
    "女性": "女性成长",
    "宝妈": "宝妈转型",
    "家庭": "家庭责任",
    "健康": "健康养老",
    "财务": "财富风险",
    "保险": "财富风险",
    "平台": "平台价值",
    "团队": "人才发展",
    "社交": "圈层社交",
    "社群": "圈层社交",
    "活动": "活动经营",
    "城市": "城市生活变化",
    "大湾区": "城市生活变化",
    "消费": "消费观念变化",
}


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def score_entry(item: dict, cluster: dict, index: int, bucket: str) -> dict:
    title = cluster.get("main_title") or item.get("original_title", "模拟热点")
    rank = int(item.get("source_rank") or 20)
    raw_hot = float(item.get("hot_score") or 60)
    hot_score = round(min(100, max(50, raw_hot + cluster.get("appear_count", 1) * 1.5)), 2)
    interest_score = round(min(100, 68 + (index % 8) * 3 + (10 - min(rank, 10)) * 0.8), 2)
    weak_connection_score = round(min(100, 62 + len(cluster.get("source_platforms", [])) * 4 + (index % 5) * 2), 2)
    safety_score = round(88 + (index % 4) * 2, 2)
    total_score = round(
        hot_score * 0.45
        + interest_score * 0.35
        + weak_connection_score * 0.15
        + safety_score * 0.05,
        2,
    )

    directions = []
    for keyword, direction in KEYWORD_DIRECTIONS.items():
        if keyword in title and direction not in directions:
            directions.append(direction)
    if not directions:
        directions.append("观察备用")
    directions = [direction for direction in directions if direction in DIRECTIONS][:3]

    if bucket == "top_inspiration":
        usage = MATERIAL_USAGE[index % 5]
        recommend_level = "high" if total_score >= 82 else "medium"
        save_to_library = True
    elif bucket == "watchlist":
        usage = "观察备用"
        recommend_level = "watch"
        save_to_library = False
    else:
        usage = MATERIAL_USAGE[index % 6]
        recommend_level = "medium" if total_score >= 72 else "low"
        save_to_library = total_score >= 78

    return {
        "original_title": title,
        "source_platform": item.get("source_platform", "模拟平台"),
        "source_rank": rank,
        "crawl_time": item.get("crawl_time"),
        "source_url": item.get("source_url"),
        "trace_url": item.get("trace_url"),
        "search_url": item.get("search_url"),
        "hotspot_summary": f"模拟分析：{title} 正在形成可观察的话题热度。",
        "why_worth_attention": "该话题连接了生活方式、职业选择与家庭责任等长期议题，适合验证灵感雷达的筛选链路。",
        "interest_point": "讨论点不只停留在事件本身，还能延展到个人决策、社群交流和内容选题。",
        "hot_score": hot_score,
        "interest_score": interest_score,
        "weak_connection_score": weak_connection_score,
        "safety_score": safety_score,
        "total_score": total_score,
        "weak_connection_directions": directions,
        "material_usage": usage,
        "inspiration_tips": [
            f"可从“{directions[0]}”角度提炼一个轻量观点。",
            "适合作为群聊破冰、短内容选题或每日观察素材。",
        ],
        "recommend_level": recommend_level,
        "risk_note": "模拟数据，仅用于链路测试；上线前需要替换为真实来源校验和人工风险审核。",
        "suggest_save_to_library": save_to_library,
        "display_bucket": BUCKETS[bucket],
    }


def build_bucket(clusters: list[dict], bucket: str, limit: int, sort_key) -> list[dict]:
    selected = sorted(clusters, key=sort_key)[:limit]
    entries = []
    for index, cluster in enumerate(selected):
        item = cluster.get("items", [{}])[0]
        entries.append(score_entry(item, cluster, index, bucket))
    return entries


def main() -> None:
    now = shanghai_now()
    date_text = now.strftime("%Y-%m-%d")
    clusters_path = Path("data") / "clusters" / f"{date_text}.json"
    clusters_payload = (
        json.loads(clusters_path.read_text(encoding="utf-8"))
        if clusters_path.exists()
        else {"clusters": []}
    )
    clusters = clusters_payload.get("clusters", [])

    top_hot = build_bucket(
        clusters,
        "top_hot",
        20,
        lambda cluster: (cluster.get("highest_rank", 999), -cluster.get("appear_count", 0)),
    )
    top_interesting = build_bucket(
        clusters,
        "top_interesting",
        20,
        lambda cluster: (-(cluster.get("items", [{}])[0].get("hot_score", 0) % 17), cluster.get("highest_rank", 999)),
    )
    top_inspiration = sorted(
        build_bucket(
            clusters,
            "top_inspiration",
            min(15, len(clusters)),
            lambda cluster: (-len(cluster.get("source_platforms", [])), cluster.get("highest_rank", 999)),
        ),
        key=lambda entry: entry["total_score"],
        reverse=True,
    )
    used_titles = {entry["original_title"] for entry in top_inspiration[:8]}
    watch_candidates = [cluster for cluster in clusters if cluster.get("main_title") not in used_titles]
    watchlist = build_bucket(
        watch_candidates,
        "watchlist",
        min(10, len(watch_candidates)),
        lambda cluster: (-cluster.get("highest_rank", 999), cluster.get("main_title", "")),
    )

    payload = {
        "date": date_text,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": MODE,
        "today_overview": {
            "summary": "今日模拟热点覆盖职业安全感、AI效率、女性成长、家庭健康、低成本社交与城市生活变化。",
            "total_clusters": len(clusters),
            "top_platforms": sorted(
                {
                    platform
                    for cluster in clusters
                    for platform in cluster.get("source_platforms", [])
                }
            ),
            "score_weights": {
                "hot_score": 0.45,
                "interest_score": 0.35,
                "weak_connection_score": 0.15,
                "safety_score": 0.05,
            },
        },
        "top_hot": top_hot,
        "top_interesting": top_interesting,
        "top_inspiration": top_inspiration[:15],
        "watchlist": watchlist,
    }

    output_dir = Path("data") / "daily"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{date_text}_analysis.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated mock inspiration analysis: {output_path}")


if __name__ == "__main__":
    main()
