import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
MODE = "mock"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def trend_for(cluster: dict) -> str:
    if cluster["appear_count"] >= 3:
        return "rising"
    if cluster["appear_count"] == 2:
        return "steady"
    return "new"


def first_non_empty(values: list[str]) -> str:
    for value in values:
        if value:
            return value
    return ""


def source_level(source_url: str, board_item_url: str, board_url: str, search_url: str) -> str:
    if source_url:
        return "original"
    if board_item_url:
        return "board_item"
    if board_url:
        return "board_page"
    if search_url:
        return "search_fallback"
    return "no_link"


def main() -> None:
    now = shanghai_now()
    date_text = now.strftime("%Y-%m-%d")
    snapshot_dir = Path("data") / "snapshots" / date_text
    snapshots = []
    for path in sorted(snapshot_dir.glob("*.json")):
        snapshots.append(json.loads(path.read_text(encoding="utf-8")))

    clusters_by_title: dict[str, dict] = {}
    for snapshot in snapshots:
        for item in snapshot.get("items", []):
            title = item.get("original_title", "").strip()
            if not title:
                continue
            cluster = clusters_by_title.setdefault(
                title,
                {
                    "cluster_id": f"cluster-{date_text}-{len(clusters_by_title) + 1:03d}",
                    "main_title": title,
                    "original_titles": [],
                    "source_platforms": [],
                    "board_names": [],
                    "first_seen": item.get("crawl_time"),
                    "last_seen": item.get("crawl_time"),
                    "highest_rank": item.get("source_rank", 999),
                    "appear_count": 0,
                    "is_multi_platform": False,
                    "heat_trend": "new",
                    "primary_source_url": "",
                    "primary_board_item_url": "",
                    "primary_board_url": "",
                    "primary_search_url": "",
                    "source_level": "no_link",
                    "source_urls": [],
                    "board_item_urls": [],
                    "board_urls": [],
                    "search_urls": [],
                    "items": [],
                },
            )
            cluster["original_titles"].append(title)
            if item.get("source_platform") not in cluster["source_platforms"]:
                cluster["source_platforms"].append(item.get("source_platform"))
            if item.get("board_name") not in cluster["board_names"]:
                cluster["board_names"].append(item.get("board_name"))
            cluster["first_seen"] = min(cluster["first_seen"], item.get("crawl_time"))
            cluster["last_seen"] = max(cluster["last_seen"], item.get("crawl_time"))
            cluster["highest_rank"] = min(cluster["highest_rank"], item.get("source_rank", 999))
            cluster["appear_count"] += 1
            if item.get("source_url"):
                cluster["source_urls"].append(item["source_url"])
            if item.get("board_item_url"):
                cluster["board_item_urls"].append(item["board_item_url"])
            if item.get("board_url"):
                cluster["board_urls"].append(item["board_url"])
            if item.get("search_url"):
                cluster["search_urls"].append(item["search_url"])
            cluster["items"].append(item)

    clusters = []
    for cluster in clusters_by_title.values():
        cluster["original_titles"] = sorted(set(cluster["original_titles"]))
        cluster["source_urls"] = sorted(set(cluster["source_urls"]))
        cluster["board_item_urls"] = sorted(set(cluster["board_item_urls"]))
        cluster["board_urls"] = sorted(set(cluster["board_urls"]))
        cluster["search_urls"] = sorted(set(cluster["search_urls"]))
        cluster["primary_source_url"] = first_non_empty(cluster["source_urls"])
        cluster["primary_board_item_url"] = first_non_empty(cluster["board_item_urls"])
        cluster["primary_board_url"] = first_non_empty(cluster["board_urls"])
        cluster["primary_search_url"] = first_non_empty(cluster["search_urls"])
        cluster["source_level"] = source_level(
            cluster["primary_source_url"],
            cluster["primary_board_item_url"],
            cluster["primary_board_url"],
            cluster["primary_search_url"],
        )
        cluster["is_multi_platform"] = len(cluster["source_platforms"]) > 1
        cluster["heat_trend"] = trend_for(cluster)
        clusters.append(cluster)

    clusters.sort(key=lambda item: (item["highest_rank"], -item["appear_count"], item["main_title"]))
    payload = {
        "date": date_text,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": MODE,
        "clusters": clusters,
    }

    output_dir = Path("data") / "clusters"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{date_text}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated mock clusters: {output_path} ({len(clusters)} clusters)")


if __name__ == "__main__":
    main()
