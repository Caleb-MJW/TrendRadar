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
                    "first_seen": item.get("crawl_time"),
                    "last_seen": item.get("crawl_time"),
                    "highest_rank": item.get("source_rank", 999),
                    "appear_count": 0,
                    "is_multi_platform": False,
                    "heat_trend": "new",
                    "primary_source_url": "",
                    "primary_trace_url": "",
                    "primary_search_url": "",
                    "source_urls": [],
                    "trace_urls": [],
                    "search_urls": [],
                    "items": [],
                },
            )
            cluster["original_titles"].append(title)
            if item.get("source_platform") not in cluster["source_platforms"]:
                cluster["source_platforms"].append(item.get("source_platform"))
            cluster["first_seen"] = min(cluster["first_seen"], item.get("crawl_time"))
            cluster["last_seen"] = max(cluster["last_seen"], item.get("crawl_time"))
            cluster["highest_rank"] = min(cluster["highest_rank"], item.get("source_rank", 999))
            cluster["appear_count"] += 1
            if item.get("source_url"):
                cluster["source_urls"].append(item["source_url"])
            if item.get("trace_url"):
                cluster["trace_urls"].append(item["trace_url"])
            elif item.get("search_url"):
                cluster["trace_urls"].append(item["search_url"])
            if item.get("search_url"):
                cluster["search_urls"].append(item["search_url"])
            cluster["items"].append(item)

    clusters = []
    for cluster in clusters_by_title.values():
        cluster["original_titles"] = sorted(set(cluster["original_titles"]))
        cluster["source_urls"] = sorted(set(cluster["source_urls"]))
        cluster["trace_urls"] = sorted(set(cluster["trace_urls"]))
        cluster["search_urls"] = sorted(set(cluster["search_urls"]))
        cluster["primary_source_url"] = first_non_empty(cluster["source_urls"])
        cluster["primary_trace_url"] = first_non_empty(cluster["trace_urls"]) or first_non_empty(cluster["search_urls"])
        cluster["primary_search_url"] = first_non_empty(cluster["search_urls"])
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
