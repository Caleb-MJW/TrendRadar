import html
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
DEFAULT_MODE = "real"
MAX_ITEMS_PER_PLATFORM = 20

BOARD_URLS = {
    "百度热搜": "https://top.baidu.com/board?tab=realtime",
    "微博热搜": "https://s.weibo.com/top/summary",
    "知乎热榜": "https://www.zhihu.com/hot",
    "B站热门": "https://www.bilibili.com/v/popular/all",
}

MOCK_TOPICS = {
    "百度热搜": [
        "为什么越来越多人关注养老规划",
        "年轻人存钱方式发生变化",
        "家庭健康管理被频繁搜索",
        "AI会影响哪些普通岗位",
        "职场人如何提高抗风险能力",
        "孩子暑期兴趣班怎么选",
        "低价旅游套餐为什么突然火了",
        "大湾区通勤生活成本被关注",
    ],
    "微博热搜": [
        "某热门剧女主选择引发网友讨论",
        "年轻人开始流行下班后轻社交",
        "体检报告里的这些信号被热议",
        "又一款 AI 应用刷屏朋友圈",
        "00后整顿职场又有新说法",
        "宝妈晒重启人生计划评论区看哭",
        "年轻人不想被消费主义推着走",
        "城市夜校报名排队到深夜",
    ],
    "知乎热榜": [
        "为什么很多人到 30 岁才开始重视职业选择权？",
        "普通人应该如何建立第二增长曲线？",
        "AI 普及后，哪些能力反而更值钱？",
        "女性重启事业，最需要解决的是什么？",
        "稳定工作和长期成长，哪个更重要？",
        "亲子教育中最容易被忽略的成本是什么？",
        "为什么低成本社交反而让人更放松？",
        "普通家庭怎样做健康和养老的长期规划？",
    ],
    "B站热门": [
        "我用 AI 重新整理了自己的工作流",
        "年轻人为什么越来越爱低成本社交",
        "普通人如何做一套人生升级系统",
        "30岁后才明白的职业真相",
        "这届年轻人开始认真研究现金流",
        "宝妈做自媒体的一天到底有多满",
        "把体检报告做成家庭健康档案",
        "城市夜校体验：陌生人如何变成同学",
    ],
}


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def http_get(url: str, *, json_mode: bool = False) -> Any:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "Referer": url,
        },
    )
    with urlopen(request, timeout=12) as response:
        raw = response.read()
    text = raw.decode("utf-8", errors="ignore")
    if json_mode:
        return json.loads(text)
    return text


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


def source_level(source_url: str, board_item_url: str, board_url: str) -> str:
    if source_url:
        return "original"
    if board_item_url:
        return "board_item"
    if board_url:
        return "board_page"
    return "no_link"


def make_item(
    *,
    mode: str,
    platform: str,
    board_name: str,
    title: str,
    rank: int,
    hot_score: int | float | str | None,
    crawl_time: str,
    source_url: str = "",
    board_item_url: str = "",
    board_url: str = "",
    tags_raw: list[str] | None = None,
) -> dict:
    level = source_level(source_url, board_item_url, board_url)
    origin_type = "hotlist" if mode == "real" else "mock_hotlist"
    stable_id = hashlib.md5(f"{mode}|{platform}|{rank}|{title}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": f"{mode}-{platform}-{rank}-{stable_id}",
        "mode": mode,
        "source_origin_type": origin_type,
        "is_reference_valid": mode == "real",
        "source_platform": platform,
        "board_name": board_name,
        "original_title": title,
        "source_rank": rank,
        "hot_score": hot_score if hot_score not in (None, "") else 0,
        "crawl_time": crawl_time,
        "source_url": source_url,
        "board_item_url": board_item_url,
        "board_url": board_url,
        "source_level": level,
        "tags_raw": tags_raw or [],
    }


def fetch_baidu(now: datetime) -> list[dict]:
    platform = "百度热搜"
    board_name = "百度热搜榜"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    text = http_get(board_url)
    matches = re.findall(r'"word"\s*:\s*"([^"]+)"(?:.*?"hotScore"\s*:\s*"?(\d+)"?)?', text)
    items = []
    seen = set()
    for title, score in matches:
        title = clean_text(title)
        if not title or title in seen:
            continue
        seen.add(title)
        rank = len(items) + 1
        items.append(
            make_item(
                mode="real",
                platform=platform,
                board_name=board_name,
                title=title,
                rank=rank,
                hot_score=int(score) if score else 0,
                crawl_time=crawl_time,
                board_url=board_url,
            )
        )
        if len(items) >= MAX_ITEMS_PER_PLATFORM:
            break
    if not items:
        raise RuntimeError("百度热搜页面未解析到榜单条目")
    return items


def fetch_weibo(now: datetime) -> list[dict]:
    platform = "微博热搜"
    board_name = "微博热搜榜"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    text = http_get(board_url)
    row_pattern = re.compile(r'<td class="td-02">.*?<a href="([^"]+)"[^>]*>(.*?)</a>(.*?)</td>', re.S)
    items = []
    seen = set()
    for href, raw_title, tail in row_pattern.findall(text):
        title = clean_text(re.sub(r"<.*?>", "", raw_title))
        if not title or title == "微博热搜" or title in seen:
            continue
        seen.add(title)
        score_match = re.search(r'<span>(\d+)</span>', tail)
        rank = len(items) + 1
        item_url = urljoin("https://s.weibo.com", href)
        items.append(
            make_item(
                mode="real",
                platform=platform,
                board_name=board_name,
                title=title,
                rank=rank,
                hot_score=int(score_match.group(1)) if score_match else 0,
                crawl_time=crawl_time,
                board_item_url=item_url,
                board_url=board_url,
            )
        )
        if len(items) >= MAX_ITEMS_PER_PLATFORM:
            break
    if not items:
        raise RuntimeError("微博热搜页面未解析到榜单条目")
    return items


def fetch_zhihu(now: datetime) -> list[dict]:
    platform = "知乎热榜"
    board_name = "知乎热榜"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    api_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20&desktop=true"
    payload = http_get(api_url, json_mode=True)
    items = []
    for entry in payload.get("data", [])[:MAX_ITEMS_PER_PLATFORM]:
        target = entry.get("target") or {}
        title = clean_text(target.get("title"))
        if not title:
            continue
        question_id = target.get("id")
        item_url = f"https://www.zhihu.com/question/{question_id}" if question_id else clean_text(target.get("url"))
        rank = len(items) + 1
        items.append(
            make_item(
                mode="real",
                platform=platform,
                board_name=board_name,
                title=title,
                rank=rank,
                hot_score=clean_text(entry.get("detail_text")),
                crawl_time=crawl_time,
                source_url=item_url,
                board_item_url=item_url,
                board_url=board_url,
            )
        )
    if not items:
        raise RuntimeError("知乎热榜接口未返回可用条目")
    return items


def fetch_bilibili(now: datetime) -> list[dict]:
    platform = "B站热门"
    board_name = "B站热门"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    api_url = "https://api.bilibili.com/x/web-interface/popular?ps=20&pn=1"
    payload = http_get(api_url, json_mode=True)
    raw_items = (payload.get("data") or {}).get("list") or []
    items = []
    for entry in raw_items[:MAX_ITEMS_PER_PLATFORM]:
        title = clean_text(entry.get("title"))
        if not title:
            continue
        bvid = clean_text(entry.get("bvid"))
        item_url = f"https://www.bilibili.com/video/{bvid}" if bvid else clean_text(entry.get("short_link_v2"))
        stat = entry.get("stat") or {}
        rank = len(items) + 1
        items.append(
            make_item(
                mode="real",
                platform=platform,
                board_name=board_name,
                title=title,
                rank=rank,
                hot_score=stat.get("view", 0),
                crawl_time=crawl_time,
                source_url=item_url,
                board_item_url=item_url,
                board_url=board_url,
            )
        )
    if not items:
        raise RuntimeError("B站热门接口未返回可用条目")
    return items


REAL_FETCHERS = [
    ("百度热搜", fetch_baidu),
    ("微博热搜", fetch_weibo),
    ("知乎热榜", fetch_zhihu),
    ("B站热门", fetch_bilibili),
]


def fetch_real(now: datetime) -> tuple[list[dict], list[dict]]:
    items = []
    sources = []
    for platform, fetcher in REAL_FETCHERS:
        try:
            platform_items = fetcher(now)
            items.extend(platform_items)
            status = "normal" if len(platform_items) >= MAX_ITEMS_PER_PLATFORM else "partial"
            error = None if platform_items else "no items fetched"
        except Exception as exc:
            platform_items = []
            status = "failed"
            error = str(exc)
        sources.append(
            {
                "platform": platform,
                "status": status,
                "fetched_count": len(platform_items),
                "source_origin_type": "hotlist",
                "last_updated": now.isoformat(),
                "error": error,
            }
        )
    return items, sources


def fetch_mock(now: datetime) -> tuple[list[dict], list[dict]]:
    items = []
    for platform, titles in MOCK_TOPICS.items():
        board_url = BOARD_URLS[platform]
        for rank, title in enumerate(titles, 1):
            item_url = f"{board_url}#mock-board-rank-{rank}-{quote(title)}"
            items.append(
                make_item(
                    mode="mock",
                    platform=platform,
                    board_name=platform,
                    title=title,
                    rank=rank,
                    hot_score=max(50, 100 - rank * 3),
                    crawl_time=now.isoformat(),
                    board_item_url=item_url,
                    board_url=board_url,
                    tags_raw=["mock_hotlist"],
                )
            )
    sources = [
        {
            "platform": platform,
            "status": "normal",
            "fetched_count": len(titles),
            "source_origin_type": "mock_hotlist",
            "last_updated": now.isoformat(),
            "error": None,
        }
        for platform, titles in MOCK_TOPICS.items()
    ]
    return items, sources


def run_mode() -> str:
    mode = os.environ.get("TRENDRADAR_MODE", DEFAULT_MODE).strip().lower()
    if mode not in {"real", "mock"}:
        raise ValueError("TRENDRADAR_MODE must be real or mock")
    return mode


def main() -> None:
    now = shanghai_now()
    mode = run_mode()
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H%M")
    output_dir = Path("data") / "snapshots" / date_text
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{time_text}.json"

    if mode == "real":
        items, sources = fetch_real(now)
    else:
        items, sources = fetch_mock(now)

    payload = {
        "date": date_text,
        "time": time_text,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": mode,
        "sources": sources,
        "items": items,
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {mode} hotspot snapshot: {output_path} ({len(items)} items)")


if __name__ == "__main__":
    main()
