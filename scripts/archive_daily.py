import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def existing_path(path: Path) -> str | None:
    return str(path) if path.exists() else None


def latest_health_files(date_text: str) -> list[str]:
    return [str(path) for path in sorted((Path("data") / "health").glob(f"{date_text}_*.json"))]


def load_mode(analysis_path: Path) -> str:
    if not analysis_path.exists():
        return "real"
    payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    return payload.get("mode", "real")


def write_archive_html(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    health_items = "".join(f"<li>{html.escape(item)}</li>" for item in payload["health_files"])
    if not health_items:
        health_items = "<li>暂无健康状态文件。</li>"
    content = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TrendRadar 每日归档 {html.escape(payload["date"])}</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2933; background: #f7f8fa; }}
    main {{ max-width: 880px; margin: 0 auto; padding: 36px 20px; }}
    h1 {{ font-size: 30px; margin-bottom: 8px; }}
    section {{ border-top: 1px solid #e4e7eb; padding-top: 18px; margin-top: 22px; }}
    .meta {{ color: #5f6c7b; }}
  </style>
</head>
<body>
  <main>
    <h1>TrendRadar 每日归档</h1>
    <p class="meta">日期：{html.escape(payload["date"])} · 生成时间：{html.escape(payload["generated_at"])} · 模式：{html.escape(payload["mode"])}</p>
    <section>
      <h2>摘要</h2>
      <p>{html.escape(payload["summary"])}</p>
    </section>
    <section>
      <h2>文件索引</h2>
      <ul>
        <li>分析文件：{html.escape(str(payload["analysis_file"]))}</li>
        <li>热点簇文件：{html.escape(str(payload["clusters_file"]))}</li>
        <li>归档页面：{html.escape(payload["archive_html"])}</li>
      </ul>
      <h3>健康状态文件</h3>
      <ul>{health_items}</ul>
    </section>
  </main>
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    now = shanghai_now()
    date_text = now.strftime("%Y-%m-%d")
    analysis_path = Path("data") / "daily" / f"{date_text}_analysis.json"
    clusters_path = Path("data") / "clusters" / f"{date_text}.json"
    archive_html_path = Path("output") / "archive" / f"{date_text}.html"
    health_files = latest_health_files(date_text)
    mode = load_mode(analysis_path)

    summary_parts = []
    summary_parts.append("分析数据已生成" if analysis_path.exists() else "分析数据暂缺")
    summary_parts.append("热点簇数据已生成" if clusters_path.exists() else "热点簇数据暂缺")
    summary_parts.append(f"健康状态文件 {len(health_files)} 份")

    payload = {
        "date": date_text,
        "generated_at": now.isoformat(),
        "mode": mode,
        "summary": "；".join(summary_parts) + f"。该归档为 {mode} 数据链路结果。",
        "analysis_file": existing_path(analysis_path),
        "clusters_file": existing_path(clusters_path),
        "health_files": health_files,
        "archive_html": str(archive_html_path),
    }

    final_dir = Path("data") / "daily"
    final_dir.mkdir(parents=True, exist_ok=True)
    final_json_path = final_dir / f"{date_text}_final.json"
    final_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_archive_html(archive_html_path, payload)
    print(f"Generated {mode} daily archive: {final_json_path}, {archive_html_path}")


if __name__ == "__main__":
    main()
