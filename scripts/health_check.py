import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
MODE = "mock"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def latest_snapshot(date_text: str) -> tuple[Path | None, dict | None]:
    snapshot_dir = Path("data") / "snapshots" / date_text
    files = sorted(snapshot_dir.glob("*.json"))
    if not files:
        return None, None
    path = files[-1]
    return path, json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    now = shanghai_now()
    date_text = now.strftime("%Y-%m-%d")
    snapshot_path, snapshot = latest_snapshot(date_text)
    snapshot_time = snapshot.get("time", now.strftime("%H%M")) if snapshot else now.strftime("%H%M")
    items = snapshot.get("items", []) if snapshot else []

    platform_counts = Counter(item.get("source_platform", "未知平台") for item in items)
    link_counts = Counter(
        item.get("source_platform", "未知平台")
        for item in items
        if item.get("source_url") or item.get("trace_url") or item.get("search_url")
    )

    sources = []
    for platform in sorted(platform_counts):
        fetched_count = platform_counts[platform]
        sources.append(
            {
                "platform": platform,
                "status": "normal",
                "fetched_count": fetched_count,
                "with_link_count": link_counts[platform],
                "candidate_count": fetched_count,
                "ai_analyzed_count": 0,
                "last_updated": snapshot.get("generated_at", now.isoformat()) if snapshot else now.isoformat(),
                "error": None,
            }
        )

    payload = {
        "date": date_text,
        "time": snapshot_time,
        "timezone": TZ_NAME,
        "generated_at": now.isoformat(),
        "mode": MODE,
        "sources": sources,
    }

    output_dir = Path("data") / "health"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{date_text}_{snapshot_time}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    source_text = snapshot_path if snapshot_path else "no snapshot found"
    print(f"Generated mock health check: {output_path} from {source_text}")


if __name__ == "__main__":
    main()
