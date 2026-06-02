import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
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

SEARCH_URLS = {
    "微博热搜": "https://s.weibo.com/weibo?q={keyword}",
    "百度热搜": "https://www.baidu.com/s?wd={keyword}",
    "抖音热点": "https://www.douyin.com/search/{keyword}",
    "小红书热点": "https://www.xiaohongshu.com/search_result?keyword={keyword}",
    "今日头条热榜": "https://www.toutiao.com/search/?keyword={keyword}",
    "腾讯热点": "https://new.qq.com/search?query={keyword}",
    "知乎热榜": "https://www.zhihu.com/search?q={keyword}",
    "B站热门": "https://search.bilibili.com/all?keyword={keyword}",
}

TYPE_DIRECTIONS = {
    "娱乐影视话题": ["女性成长", "家庭责任", "圈层社交"],
    "女性成长话题": ["女性成长", "成长转型", "职业选择"],
    "女性成长": ["女性成长", "成长转型", "职业选择"],
    "宝妈/家庭话题": ["宝妈转型", "家庭责任", "女性成长"],
    "职场变化话题": ["职业选择", "人才发展", "AI时代变化"],
    "AI科技话题": ["AI时代变化", "人才发展", "平台价值"],
    "健康养老话题": ["健康养老", "家庭责任", "财富风险"],
    "消费观念话题": ["消费观念变化", "财富风险", "圈层社交"],
    "城市生活/社交话题": ["城市生活变化", "圈层社交", "活动经营"],
    "亲子教育话题": ["家庭责任", "宝妈转型", "活动经营"],
    "财经/收入安全感话题": ["财富风险", "职业选择", "家庭责任"],
    "社会情绪话题": ["职业选择", "圈层社交", "观察备用"],
    "年轻人生活方式话题": ["消费观念变化", "城市生活变化", "圈层社交"],
}

TYPE_COPY = {
    "娱乐影视话题": {
        "summary": "它的价值不在剧情或综艺本身，而在于把关系边界、人生选择和女性成长推到了大众讨论里。",
        "why": "娱乐话题传播快、情绪入口低，适合观察用户如何从轻松内容里谈到真实生活困惑。",
        "interest": "看点在评论区的立场分化：有人代入角色，有人讨论现实关系，也有人转向自我选择。",
        "tips": [
            "可以从“角色选择为什么会戳中现实生活”切入，做一条轻观点。",
            "适合在朋友圈延展成：一部剧真正火的不是剧情，而是大家借它说自己的生活。",
            "可以作为社群话题，引出女性成长和家庭分工的边界感讨论。",
        ],
    },
    "女性成长话题": {
        "summary": "这个话题把自我成长、职业选择和生活压力放在同一个真实场景里，容易激发共鸣。",
        "why": "女性成长类话题常常同时连接家庭、收入、年龄焦虑和自我实现，灵感延展空间很大。",
        "interest": "趣味点在于它不是宏大叙事，而是从一个具体年龄、身份或选择切进生活现场。",
        "tips": [
            "可以从“重新规划不是失败，而是开始拥有选择权”这个角度延展。",
            "适合做一条朋友圈轻观点：30岁以后真正重要的是给自己留余地。",
            "可以沉淀成女性成长素材，讨论如何把焦虑转成可执行的小计划。",
        ],
    },
    "宝妈/家庭话题": {
        "summary": "这个热点有生活现场感，能把宝妈转型、家庭责任和收入安全感自然串起来。",
        "why": "家庭类话题容易触发真实经验分享，既有情绪共鸣，也有行动建议的空间。",
        "interest": "看点在于评论区往往会出现两种声音：一边是现实压力，一边是重新开始的勇气。",
        "tips": [
            "可以从“妈妈重新出发，最难的是时间和支持系统”展开。",
            "适合做早会破冰：家庭责任怎样影响一个人的职业选择。",
            "可以转成活动经营素材，设计一场宝妈成长或家庭健康主题分享。",
        ],
    },
    "职场变化话题": {
        "summary": "它能引出职业安全感从“岗位稳定”转向“能力和选择权稳定”的讨论。",
        "why": "职场变化是高频公共焦虑，适合观察普通人如何理解风险、效率和长期成长。",
        "interest": "趣味点在于年轻人不再只问工资，也开始问边界、成长、现金流和可替代性。",
        "tips": [
            "可以从“安全感不是不变，而是自己还有选择”这个角度延展。",
            "适合做工作群话题：哪些能力能让普通人在变化里更稳。",
            "可以沉淀成专业观点素材，讨论职业选择权比岗位标签更重要。",
        ],
    },
    "AI科技话题": {
        "summary": "这个热点的灵感价值在于，它能自然引出普通人如何提升效率、重新规划能力结构。",
        "why": "AI话题自带传播热度，但真正有价值的是把工具变化翻译成普通人的可执行动作。",
        "interest": "看点在于大家既兴奋又担心：有人晒效率提升，也有人担心岗位被替代。",
        "tips": [
            "可以做一条短视频选题：AI到底替代工作，还是替代不会用AI的人。",
            "适合早会引出团队效率讨论：先把一个重复流程交给工具试试。",
            "可以延展到人才发展：未来更值钱的是判断力、表达力和工具协作力。",
        ],
    },
    "健康养老话题": {
        "summary": "它适合沉淀为家庭责任和长期规划类素材，但表达时要避免制造焦虑。",
        "why": "健康与养老话题关注度稳定，能把个人生活、家庭角色和财务准备连接起来。",
        "interest": "趣味点在于年轻人也开始参与讨论，说明健康规划不再只是长辈议题。",
        "tips": [
            "可以从“家庭健康管理不是焦虑清单，而是提前准备”切入。",
            "适合做朋友圈观点：体检报告背后是一个家庭的长期责任。",
            "可以设计成家庭健康档案或养老规划的轻量内容素材。",
        ],
    },
    "消费观念话题": {
        "summary": "这个话题反映了消费从面子、冲动转向预算、体验和长期安全感。",
        "why": "消费变化能直接映射社会情绪，适合观察年轻人如何重新定义体面生活。",
        "interest": "看点在于“低成本”不等于将就，而是大家在寻找更可控的生活方式。",
        "tips": [
            "可以从“低成本不是降低生活，而是提高掌控感”延展。",
            "适合做朋友圈轻观点：越来越多人开始把钱花在真正需要的地方。",
            "可以作为社群讨论：哪些消费正在从炫耀变成自我照顾。",
        ],
    },
    "城市生活/社交话题": {
        "summary": "它把城市生活、兴趣社交和真实连接放在一起，适合观察线下活动需求。",
        "why": "城市社交话题兼具生活感和活动经营价值，容易从热闹讨论转为具体行动。",
        "interest": "趣味点在于年轻人不是不社交，而是更喜欢低压力、有主题、有边界的连接。",
        "tips": [
            "可以作为早会破冰，引出“活动经营不是销售动作，而是建立真实连接”。",
            "适合做短视频选题：为什么城市夜校和兴趣局突然变得受欢迎。",
            "可以延展为圈层社交素材，讨论熟人关系之外的新连接方式。",
        ],
    },
    "亲子教育话题": {
        "summary": "这个话题容易引出家长对教育成本、陪伴质量和孩子长期成长的真实纠结。",
        "why": "亲子教育既有搜索热度，也有强讨论性，适合测试系统对家庭场景的理解。",
        "interest": "看点在于家长不只在比较价格，也在重新思考什么才是有效陪伴。",
        "tips": [
            "可以从“陪伴质量不一定和花费成正比”切入。",
            "适合做家庭群或社群话题：孩子真正需要的是课程，还是稳定互动。",
            "可以沉淀为活动主题，比如低成本亲子周末计划。",
        ],
    },
    "财经/收入安全感话题": {
        "summary": "这个话题把收入、储蓄、副业和风险意识放到台面上，讨论密度很高。",
        "why": "收入安全感是强现实议题，能自然连接职业选择、家庭责任和长期规划。",
        "interest": "趣味点在于大家不再只讨论赚多少钱，也讨论现金流、Plan B 和抗风险能力。",
        "tips": [
            "可以从“人生 Plan B 不是悲观，而是给自己多一个缓冲”延展。",
            "适合做工作群话题：普通人能做哪些低门槛抗风险准备。",
            "可以作为专业观点素材，把收入安全感拆成能力、现金流和家庭保障。",
        ],
    },
}

DEFAULT_COPY = {
    "summary": "这个热点有明显的大众讨论入口，适合用来测试灵感雷达从热度到观点的转化。",
    "why": "它兼具话题性和生活关联，能作为轻观点、群聊话题或观察备用素材。",
    "interest": "趣味点在于不同人会从各自处境出发解读同一个标题。",
    "tips": [
        "可以先抓住评论区最有分歧的一句话，再延展成轻观点。",
        "适合放进观察备用，等待后续热度或真实案例补充。",
        "可以从用户身份切入，看看它和职业、家庭或消费选择有什么关系。",
    ],
}


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def fallback_search_url(platform: str, title: str) -> str:
    template = SEARCH_URLS.get(platform, "https://www.baidu.com/s?wd={keyword}")
    return template.format(keyword=quote(title))


def topic_type(item: dict) -> str:
    tags = item.get("tags_raw") or []
    for tag in tags:
        if tag in TYPE_COPY:
            return tag
    if "女性成长" in tags:
        return "女性成长话题"
    return tags[0] if tags else "观察备用"


def directions_for(item: dict) -> list[str]:
    tags = item.get("tags_raw") or []
    directions = []
    for tag in tags:
        for direction in TYPE_DIRECTIONS.get(tag, []):
            if direction in DIRECTIONS and direction not in directions:
                directions.append(direction)
    if not directions:
        directions.append("观察备用")
    return directions[:3]


def source_fields(item: dict, cluster: dict, title: str, platform: str) -> tuple[str, str, str]:
    search_url = item.get("search_url") or cluster.get("primary_search_url") or fallback_search_url(platform, title)
    source_url = item.get("source_url") or cluster.get("primary_source_url") or ""
    trace_url = item.get("trace_url") or cluster.get("primary_trace_url") or search_url
    return source_url, trace_url, search_url


def score_entry(item: dict, cluster: dict, index: int, bucket: str) -> dict:
    title = cluster.get("main_title") or item.get("original_title", "模拟热点")
    platform = item.get("source_platform", "模拟平台")
    rank = int(item.get("source_rank") or cluster.get("highest_rank") or 20)
    raw_hot = float(item.get("hot_score") or 60)
    hot_score = round(min(100, max(50, raw_hot + cluster.get("appear_count", 1) * 1.2)), 2)
    interest_score = round(min(100, 72 + (index % 9) * 2.4 + (9 - min(rank, 9)) * 0.9), 2)
    weak_connection_score = round(min(100, 60 + len(directions_for(item)) * 6 + (index % 4) * 2.5), 2)
    safety_score = round(86 + (index % 5) * 2, 2)
    total_score = round(
        hot_score * 0.45
        + interest_score * 0.35
        + weak_connection_score * 0.15
        + safety_score * 0.05,
        2,
    )

    copy = TYPE_COPY.get(topic_type(item), DEFAULT_COPY)
    directions = directions_for(item)
    source_url, trace_url, search_url = source_fields(item, cluster, title, platform)

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
        recommend_level = "medium" if total_score >= 74 else "low"
        save_to_library = total_score >= 80

    return {
        "original_title": title,
        "source_platform": platform,
        "source_rank": rank,
        "crawl_time": item.get("crawl_time"),
        "source_url": source_url,
        "trace_url": trace_url,
        "search_url": search_url,
        "hotspot_summary": copy["summary"],
        "why_worth_attention": copy["why"],
        "interest_point": copy["interest"],
        "hot_score": hot_score,
        "interest_score": interest_score,
        "weak_connection_score": weak_connection_score,
        "safety_score": safety_score,
        "total_score": total_score,
        "weak_connection_directions": directions,
        "material_usage": usage,
        "inspiration_tips": copy["tips"],
        "recommend_level": recommend_level,
        "risk_note": "模拟数据，仅用于链路测试；发布真实内容前仍需核验来源、语境和潜在争议。",
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
        lambda cluster: (
            -len((cluster.get("items", [{}])[0].get("tags_raw") or [])),
            -(cluster.get("items", [{}])[0].get("hot_score", 0) % 19),
            cluster.get("highest_rank", 999),
        ),
    )
    top_inspiration = sorted(
        build_bucket(
            clusters,
            "top_inspiration",
            min(15, len(clusters)),
            lambda cluster: (
                -len(directions_for(cluster.get("items", [{}])[0])),
                cluster.get("highest_rank", 999),
            ),
        ),
        key=lambda entry: entry["total_score"],
        reverse=True,
    )
    used_titles = {entry["original_title"] for entry in top_hot[:8] + top_inspiration[:8]}
    watch_candidates = [cluster for cluster in clusters if cluster.get("main_title") not in used_titles]
    watchlist = build_bucket(
        watch_candidates,
        "watchlist",
        min(12, len(watch_candidates)),
        lambda cluster: (-cluster.get("highest_rank", 999), cluster.get("main_title", "")),
    )

    payload = {
        "date": date_text,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": MODE,
        "today_overview": {
            "summary": "今日模拟热点更接近真实热榜生态：娱乐影视、AI工具、女性成长、宝妈家庭、亲子教育、健康养老、消费变化、城市社交和收入安全感都有覆盖。",
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
