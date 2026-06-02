import hashlib
import html
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin
from zoneinfo import ZoneInfo

try:
    import requests
except ImportError:  # Diagnostics still need to be written when dependencies are missing.
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # HTML parsers will report this in diagnostics.
    BeautifulSoup = None


TZ_NAME = "Asia/Shanghai"
DEFAULT_MODE = "real"
MAX_ITEMS_PER_PLATFORM = 20
REQUEST_TIMEOUT_SECONDS = 15

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

JSON_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "application/json, text/plain, */*",
}

BOARD_URLS = {
    "百度热搜": "https://top.baidu.com/board?tab=realtime",
    "微博热搜": "https://s.weibo.com/top/summary?cate=realtimehot",
    "知乎热榜": "https://www.zhihu.com/billboard",
    "B站热门": "https://www.bilibili.com/v/popular/rank/all",
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


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def source_level(source_url: str, board_item_url: str, board_url: str) -> str:
    if source_url:
        return "original"
    if board_item_url:
        return "board_item"
    if board_url:
        return "board_page"
    return "no_link"


def base_diagnostic(platform: str, url: str, now: datetime) -> dict:
    return {
        "platform": platform,
        "status": "failed",
        "attempted_url": url,
        "request_method": "GET",
        "http_status": None,
        "content_type": None,
        "final_url": None,
        "response_length": None,
        "page_title": None,
        "exception_type": None,
        "error": None,
        "elapsed_ms": None,
        "fetched_count": 0,
        "parser_status": "not_run",
        "parser_error": None,
        "debug_hint": {},
        "parser_candidates_count": 0,
        "source_origin_type": "hotlist",
        "last_updated": now.isoformat(),
    }


def page_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return clean_text(match.group(1)) if match else ""


def request_hotlist(
    platform: str,
    url: str,
    now: datetime,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[str, dict]:
    diagnostic = base_diagnostic(platform, url, now)
    if requests is None:
        diagnostic["exception_type"] = "ModuleNotFoundError"
        diagnostic["error"] = "requests is not installed"
        return "", diagnostic

    started = time.perf_counter()
    try:
        response = requests.get(
            url,
            headers=headers or REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        diagnostic["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
        diagnostic["http_status"] = response.status_code
        diagnostic["content_type"] = response.headers.get("content-type")
        diagnostic["final_url"] = response.url
        diagnostic["response_length"] = len(response.text)
        diagnostic["page_title"] = page_title(response.text)
        response.raise_for_status()
        return response.text, diagnostic
    except Exception as exc:
        diagnostic["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
        diagnostic["exception_type"] = type(exc).__name__
        diagnostic["error"] = str(exc)
        if getattr(exc, "response", None) is not None:
            diagnostic["http_status"] = exc.response.status_code
            diagnostic["content_type"] = exc.response.headers.get("content-type")
            diagnostic["final_url"] = exc.response.url
            diagnostic["response_length"] = len(exc.response.text)
            diagnostic["page_title"] = page_title(exc.response.text)
        return "", diagnostic


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


def parser_diagnostic(
    diagnostic: dict,
    items: list[dict],
    parser_error: str | None = None,
    *,
    candidates_count: int | None = None,
    debug_hint: dict | None = None,
) -> dict:
    diagnostic["fetched_count"] = len(items)
    if candidates_count is not None:
        diagnostic["parser_candidates_count"] = candidates_count
    if debug_hint is not None:
        diagnostic["debug_hint"] = debug_hint
    if parser_error:
        diagnostic["parser_status"] = "failed" if not items else "partial"
        diagnostic["parser_error"] = parser_error
    elif len(items) >= MAX_ITEMS_PER_PLATFORM:
        diagnostic["parser_status"] = "success"
    elif items:
        diagnostic["parser_status"] = "partial"
        diagnostic["parser_error"] = f"parsed only {len(items)} items"
    else:
        diagnostic["parser_status"] = "failed"
        diagnostic["parser_error"] = "no hotlist items parsed"

    if not items:
        diagnostic["status"] = "failed"
    elif len(items) >= MAX_ITEMS_PER_PLATFORM:
        diagnostic["status"] = "normal"
    else:
        diagnostic["status"] = "partial"
    return diagnostic


def parse_json_objects(text: str, key: str) -> list[dict]:
    decoder = json.JSONDecoder()
    objects = []
    start = 0
    while True:
        index = text.find(key, start)
        if index == -1:
            break
        brace = text.rfind("{", 0, index)
        if brace == -1:
            start = index + len(key)
            continue
        try:
            obj, end = decoder.raw_decode(text[brace:])
            if isinstance(obj, dict):
                objects.append(obj)
            start = brace + end
        except json.JSONDecodeError:
            start = index + len(key)
    return objects


def fetch_baidu(now: datetime) -> tuple[list[dict], dict]:
    platform = "百度热搜"
    board_name = "百度热搜榜"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    text, diagnostic = request_hotlist(platform, board_url, now)
    if not text:
        return [], diagnostic

    items = []
    seen = set()
    matches = re.findall(r'"word"\s*:\s*"([^"]+)"(?:.*?"hotScore"\s*:\s*"?(\d+)"?)?', text)
    for title, score in matches:
        title = clean_text(title)
        if not title or title in seen:
            continue
        seen.add(title)
        items.append(
            make_item(
                mode="real",
                platform=platform,
                board_name=board_name,
                title=title,
                rank=len(items) + 1,
                hot_score=int(score) if score else 0,
                crawl_time=crawl_time,
                board_url=board_url,
            )
        )
        if len(items) >= MAX_ITEMS_PER_PLATFORM:
            break
    diagnostic["debug_hint"] = {
        "contains_word": '"word"' in text,
        "contains_hotScore": "hotScore" in text,
        "contains_realtime": "realtime" in text,
    }
    return items, parser_diagnostic(diagnostic, items, candidates_count=len(matches), debug_hint=diagnostic["debug_hint"])


def fetch_weibo(now: datetime) -> tuple[list[dict], dict]:
    platform = "微博热搜"
    board_name = "微博热搜榜"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    text, diagnostic = request_hotlist(platform, board_url, now)
    if not text:
        return [], diagnostic

    if BeautifulSoup is None:
        return [], parser_diagnostic(
            diagnostic,
            [],
            "beautifulsoup4 is not installed",
            candidates_count=0,
            debug_hint={
                "contains_td_02": "td-02" in text,
                "contains_realtimehot": "realtimehot" in text,
                "contains_weibo_q": "/weibo?q=" in text or "weibo?q=" in text,
                "contains_hot_search": "热搜" in text,
            },
        )

    soup = BeautifulSoup(text, "html.parser")
    candidate_links = []
    for link in soup.select("td.td-02 a[href]"):
        href = link.get("href") or ""
        if "/weibo?q=" in href or "weibo?q=" in href:
            candidate_links.append(link)
    if not candidate_links:
        for link in soup.select('a[href*="/weibo?q="], a[href*="weibo?q="]'):
            candidate_links.append(link)

    items = []
    seen = set()
    excluded_titles = {"微博热搜", "热搜榜", "更多", "广告", "置顶", "实时热点"}
    for link in candidate_links:
        href = link.get("href") or ""
        title = clean_text(link.get_text(" "))
        if (
            not title
            or title in excluded_titles
            or title in seen
            or title.startswith("#")
            or len(title) < 2
        ):
            continue
        seen.add(title)
        item_url = urljoin("https://s.weibo.com", href)
        items.append(
            make_item(
                mode="real",
                platform=platform,
                board_name=board_name,
                title=title,
                rank=len(items) + 1,
                hot_score=0,
                crawl_time=crawl_time,
                source_url=item_url,
                board_item_url=item_url,
                board_url=board_url,
            )
        )
        if len(items) >= MAX_ITEMS_PER_PLATFORM:
            break
    debug_hint = {
        "contains_td_02": "td-02" in text,
        "contains_realtimehot": "realtimehot" in text,
        "contains_weibo_q": "/weibo?q=" in text or "weibo?q=" in text,
        "contains_hot_search": "热搜" in text,
    }
    parser_error = None if items else "no weibo hotlist candidates parsed"
    return items, parser_diagnostic(
        diagnostic,
        items,
        parser_error,
        candidates_count=len(candidate_links),
        debug_hint=debug_hint,
    )


def fetch_zhihu(now: datetime) -> tuple[list[dict], dict]:
    platform = "知乎热榜"
    board_name = "知乎热榜"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    api_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20&desktop=true"
    headers = {
        **JSON_REQUEST_HEADERS,
        "Referer": board_url,
        "Origin": "https://www.zhihu.com",
    }
    text, diagnostic = request_hotlist(platform, api_url, now, headers=headers)
    if not text:
        return [], diagnostic

    items = []
    candidates_count = 0
    parser_error = None
    try:
        payload = json.loads(text)
        data = payload.get("data") or []
        candidates_count = len(data)
        for entry in data[:MAX_ITEMS_PER_PLATFORM]:
            target = entry.get("target") or {}
            title = clean_text(target.get("title"))
            if not title:
                continue
            question_id = target.get("id")
            item_url = f"https://www.zhihu.com/question/{question_id}" if question_id else clean_text(target.get("url"))
            items.append(
                make_item(
                    mode="real",
                    platform=platform,
                    board_name=board_name,
                    title=title,
                    rank=len(items) + 1,
                    hot_score=clean_text(entry.get("detail_text")) or max(1, 100 - len(items)),
                    crawl_time=crawl_time,
                    source_url=item_url,
                    board_item_url=item_url,
                    board_url=board_url,
                )
            )
    except Exception as exc:
        parser_error = f"zhihu json parse failed: {type(exc).__name__}: {exc}"
    debug_hint = {
        "contains_hot_lists": "hot-lists" in diagnostic.get("attempted_url", ""),
        "contains_topstory": "topstory" in diagnostic.get("attempted_url", ""),
        "contains_target": '"target"' in text,
        "contains_title": '"title"' in text,
    }
    return items, parser_diagnostic(diagnostic, items, parser_error, candidates_count=candidates_count, debug_hint=debug_hint)


def fetch_bilibili(now: datetime) -> tuple[list[dict], dict]:
    platform = "B站热门"
    board_name = "B站热门"
    board_url = BOARD_URLS[platform]
    crawl_time = now.isoformat()
    api_url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
    headers = {
        **JSON_REQUEST_HEADERS,
        "Referer": board_url,
        "Origin": "https://www.bilibili.com",
    }
    text, diagnostic = request_hotlist(platform, api_url, now, headers=headers)
    if not text:
        page_text, page_diagnostic = request_hotlist(platform, board_url, now)
        if not page_text:
            return [], diagnostic
        diagnostic = page_diagnostic
        text = page_text

    items = []
    candidates_count = 0
    parser_error = None
    try:
        payload = json.loads(text)
        data = payload.get("data") or {}
        raw_items = data.get("list") or []
        candidates_count = len(raw_items)
        for entry in raw_items[:MAX_ITEMS_PER_PLATFORM]:
            title = clean_text(entry.get("title"))
            bvid = clean_text(entry.get("bvid"))
            if not title or not bvid:
                continue
            item_url = f"https://www.bilibili.com/video/{bvid}"
            stat = entry.get("stat") or {}
            items.append(
                make_item(
                    mode="real",
                    platform=platform,
                    board_name=board_name,
                    title=title,
                    rank=len(items) + 1,
                    hot_score=stat.get("view", entry.get("score", 0)) if isinstance(stat, dict) else entry.get("score", 0),
                    crawl_time=crawl_time,
                    source_url=item_url,
                    board_item_url=item_url,
                    board_url=board_url,
                )
            )
    except Exception as exc:
        parser_error = f"bilibili json parse failed: {type(exc).__name__}: {exc}"
        objects = parse_json_objects(text, '"title"')
        candidates_count = len(objects)
        seen = set()
        for obj in objects:
            title = clean_text(obj.get("title"))
            bvid = clean_text(obj.get("bvid"))
            if not title or title in seen or not bvid:
                continue
            seen.add(title)
            item_url = f"https://www.bilibili.com/video/{bvid}"
            stat = obj.get("stat") or {}
            items.append(
                make_item(
                    mode="real",
                    platform=platform,
                    board_name=board_name,
                    title=title,
                    rank=len(items) + 1,
                    hot_score=stat.get("view", 0) if isinstance(stat, dict) else 0,
                    crawl_time=crawl_time,
                    source_url=item_url,
                    board_item_url=item_url,
                    board_url=board_url,
                )
            )
            if len(items) >= MAX_ITEMS_PER_PLATFORM:
                break
    debug_hint = {
        "contains_initial_state": "__INITIAL_STATE__" in text,
        "contains_ranking": "ranking" in text,
        "contains_bvid": "bvid" in text,
        "contains_popular": "popular" in text,
    }
    if items:
        parser_error = None
    return items, parser_diagnostic(diagnostic, items, parser_error, candidates_count=candidates_count, debug_hint=debug_hint)


REAL_FETCHERS = [
    ("百度热搜", fetch_baidu),
    ("微博热搜", fetch_weibo),
    ("知乎热榜", fetch_zhihu),
    ("B站热门", fetch_bilibili),
]


def fetch_real(now: datetime) -> tuple[list[dict], list[dict]]:
    items = []
    diagnostics = []
    for _, fetcher in REAL_FETCHERS:
        platform_items, diagnostic = fetcher(now)
        items.extend(platform_items)
        diagnostics.append(diagnostic)
    return items, diagnostics


def fetch_mock(now: datetime) -> tuple[list[dict], list[dict]]:
    items = []
    diagnostics = []
    for platform, titles in MOCK_TOPICS.items():
        board_url = BOARD_URLS[platform]
        platform_items = []
        for rank, title in enumerate(titles, 1):
            item_url = f"{board_url}#mock-board-rank-{rank}-{quote(title)}"
            platform_items.append(
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
        items.extend(platform_items)
        diagnostic = base_diagnostic(platform, board_url, now)
        diagnostic.update(
            {
                "status": "normal",
                "http_status": 200,
                "elapsed_ms": 0,
                "fetched_count": len(platform_items),
                "parser_status": "success",
                "source_origin_type": "mock_hotlist",
                "error": None,
            }
        )
        diagnostics.append(diagnostic)
    return items, diagnostics


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
        items, diagnostics = fetch_real(now)
    else:
        items, diagnostics = fetch_mock(now)

    payload = {
        "date": date_text,
        "time": time_text,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": mode,
        "fetch_diagnostics": diagnostics,
        "sources": diagnostics,
        "items": items,
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {mode} hotspot snapshot: {output_path} ({len(items)} items)")


if __name__ == "__main__":
    main()
