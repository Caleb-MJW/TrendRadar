import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
PHASE_ONE_PLATFORMS = ["百度热搜", "微博热搜", "知乎热榜", "B站热门"]


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def latest_snapshot(date_text: str) -> tuple[Path | None, dict | None]:
    snapshot_dir = Path("data") / "snapshots" / date_text
    files = sorted(snapshot_dir.glob("*.json"))
    if not files:
        return None, None
    path = files[-1]
    return path, json.loads(path.read_text(encoding="utf-8"))


def status_for(source_status: str | None, fetched_count: int) -> str:
    if source_status in {"failed", "disabled"}:
        return source_status
    if fetched_count <= 0:
        return "failed"
    if source_status == "partial" or fetched_count < 20:
        return "partial"
    return "normal"


def main() -> None:
    now = shanghai_now()
    date_text = now.strftime("%Y-%m-%d")
    snapshot_path, snapshot = latest_snapshot(date_text)
    snapshot_time = snapshot.get("time", now.strftime("%H%M")) if snapshot else now.strftime("%H%M")
    mode = snapshot.get("mode", "real") if snapshot else "real"
    items = snapshot.get("items", []) if snapshot else []
    source_meta = {source.get("platform"): source for source in snapshot.get("sources", [])} if snapshot else {}

    platform_counts = Counter(item.get("source_platform", "未知平台") for item in items)
    with_source_url = Counter(item.get("source_platform", "未知平台") for item in items if item.get("source_url"))
    with_board_item_url = Counter(
        item.get("source_platform", "未知平台") for item in items if item.get("board_item_url")
    )
    with_board_url = Counter(item.get("source_platform", "未知平台") for item in items if item.get("board_url"))
    origin_types: dict[str, set[str]] = defaultdict(set)
    for item in items:
        origin_types[item.get("source_platform", "未知平台")].add(item.get("source_origin_type", "unknown"))

    sources = []
    for platform in PHASE_ONE_PLATFORMS:
        meta = source_meta.get(platform, {})
        fetched_count = platform_counts[platform]
        status = status_for(meta.get("status"), fetched_count)
        origin_text = ",".join(sorted(origin_types[platform])) if origin_types[platform] else meta.get("source_origin_type", "hotlist")
        sources.append(
            {
                "platform": platform,
                "status": status,
                "fetched_count": fetched_count,
                "with_source_url_count": with_source_url[platform],
                "with_board_item_url_count": with_board_item_url[platform],
                "with_board_url_count": with_board_url[platform],
                "source_origin_type": origin_text,
                "last_updated": meta.get("last_updated") or snapshot.get("generated_at", now.isoformat()) if snapshot else now.isoformat(),
                "error": meta.get("error") if status in {"failed", "partial"} else None,
            }
        )

    payload = {
        "date": date_text,
        "time": snapshot_time,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": mode,
        "sources": sources,
    }

    output_dir = Path("data") / "health"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{date_text}_{snapshot_time}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    source_text = snapshot_path if snapshot_path else "no snapshot found"
    print(f"Generated health check: {output_path} from {source_text}")


if __name__ == "__main__":
    main()
