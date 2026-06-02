import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
MODE_LABEL = "模拟数据 / mock mode"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo(TZ_NAME))


def latest_health(date_text: str) -> dict:
    files = sorted((Path("data") / "health").glob(f"{date_text}_*.json"))
    if not files:
        return {"sources": []}
    return json.loads(files[-1].read_text(encoding="utf-8"))


def load_analysis(date_text: str) -> dict:
    path = Path("data") / "daily" / f"{date_text}_analysis.json"
    if not path.exists():
        return {
            "date": date_text,
            "generated_at": shanghai_now().isoformat(),
            "mode": "mock",
            "today_overview": {"summary": "暂无分析数据。", "total_clusters": 0},
            "top_hot": [],
            "top_interesting": [],
            "top_inspiration": [],
            "watchlist": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown_section(title: str, entries: list[dict]) -> str:
    lines = [f"## {title}", ""]
    if not entries:
        return "\n".join(lines + ["暂无数据。", ""])
    for index, entry in enumerate(entries, 1):
        lines.extend(
            [
                f"{index}. **{entry['original_title']}**",
                f"   - 平台: {entry['source_platform']} | 排名: {entry['source_rank']} | 总分: {entry['total_score']}",
                f"   - 摘要: {entry['hotspot_summary']}",
                f"   - 用途: {entry['material_usage']} | 关联: {'、'.join(entry['weak_connection_directions'])}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def render_markdown(analysis: dict, health: dict, generated_at: str) -> str:
    overview = analysis.get("today_overview", {})
    lines = [
        "# 今日热点灵感雷达",
        "",
        f"- 生成时间: {generated_at}",
        f"- 当前模式: {MODE_LABEL}",
        f"- 今日总览: {overview.get('summary', '暂无总览。')}",
        f"- 热点簇数量: {overview.get('total_clusters', 0)}",
        "",
        render_markdown_section("今日全网最热 TOP20", analysis.get("top_hot", [])),
        render_markdown_section("今日热门有趣 TOP20", analysis.get("top_interesting", [])),
        render_markdown_section("今日优增灵感 TOP15", analysis.get("top_inspiration", [])),
        render_markdown_section("今日观察备用", analysis.get("watchlist", [])),
        "## 信息源健康状态摘要",
        "",
    ]
    sources = health.get("sources", [])
    if sources:
        for source in sources:
            lines.append(
                f"- {source['platform']}: {source['status']}，抓取 {source['fetched_count']} 条，候选 {source['candidate_count']} 条"
            )
    else:
        lines.append("- 暂无健康状态数据。")
    lines.append("")
    return "\n".join(lines)


def render_cards(entries: list[dict]) -> str:
    if not entries:
        return "<p>暂无数据。</p>"
    cards = []
    for index, entry in enumerate(entries, 1):
        title = html.escape(entry["original_title"])
        summary = html.escape(entry["hotspot_summary"])
        directions = "、".join(html.escape(item) for item in entry["weak_connection_directions"])
        cards.append(
            f"""
            <article class="item">
              <div class="rank">{index}</div>
              <div>
                <h3>{title}</h3>
                <p>{summary}</p>
                <p class="meta">{html.escape(entry['source_platform'])} · 排名 {entry['source_rank']} · 总分 {entry['total_score']} · {html.escape(entry['material_usage'])} · {directions}</p>
              </div>
            </article>
            """
        )
    return "\n".join(cards)


def render_html(analysis: dict, health: dict, generated_at: str) -> str:
    overview = analysis.get("today_overview", {})
    health_rows = "\n".join(
        f"<tr><td>{html.escape(source['platform'])}</td><td>{html.escape(source['status'])}</td><td>{source['fetched_count']}</td><td>{source['candidate_count']}</td><td>{source['ai_analyzed_count']}</td></tr>"
        for source in health.get("sources", [])
    )
    if not health_rows:
        health_rows = '<tr><td colspan="5">暂无健康状态数据。</td></tr>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>今日热点灵感雷达</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2933; background: #f7f8fa; }}
    header {{ padding: 32px 20px 20px; background: #ffffff; border-bottom: 1px solid #e4e7eb; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 24px 20px 48px; }}
    h1 {{ margin: 0 0 12px; font-size: 32px; }}
    h2 {{ margin: 32px 0 14px; font-size: 22px; }}
    h3 {{ margin: 0 0 8px; font-size: 17px; }}
    p {{ line-height: 1.65; }}
    .meta, .mode {{ color: #5f6c7b; font-size: 14px; }}
    .overview {{ font-size: 17px; max-width: 880px; }}
    .item {{ display: grid; grid-template-columns: 42px 1fr; gap: 14px; padding: 16px 0; border-top: 1px solid #e4e7eb; }}
    .rank {{ width: 32px; height: 32px; border-radius: 6px; background: #1f2933; color: white; display: grid; place-items: center; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ padding: 10px 12px; border: 1px solid #e4e7eb; text-align: left; }}
    th {{ background: #eef2f6; }}
  </style>
</head>
<body>
  <header>
    <main>
      <h1>今日热点灵感雷达</h1>
      <p class="mode">生成时间：{html.escape(generated_at)} · 当前模式：{MODE_LABEL}</p>
      <p class="overview">{html.escape(overview.get("summary", "暂无总览。"))}</p>
    </main>
  </header>
  <main>
    <h2>今日总览</h2>
    <p>热点簇数量：{overview.get("total_clusters", 0)}</p>

    <h2>今日全网最热 TOP20</h2>
    {render_cards(analysis.get("top_hot", []))}

    <h2>今日热门有趣 TOP20</h2>
    {render_cards(analysis.get("top_interesting", []))}

    <h2>今日优增灵感 TOP15</h2>
    {render_cards(analysis.get("top_inspiration", []))}

    <h2>今日观察备用</h2>
    {render_cards(analysis.get("watchlist", []))}

    <h2>信息源健康状态摘要</h2>
    <table>
      <thead><tr><th>平台</th><th>状态</th><th>抓取数</th><th>候选数</th><th>AI分析数</th></tr></thead>
      <tbody>{health_rows}</tbody>
    </table>
  </main>
</body>
</html>
"""


def main() -> None:
    now = shanghai_now()
    date_text = now.strftime("%Y-%m-%d")
    generated_at = now.isoformat()
    analysis = load_analysis(date_text)
    health = latest_health(date_text)

    markdown = render_markdown(analysis, health, generated_at)
    page = render_html(analysis, health, generated_at)

    Path("output").mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("output/today.md").write_text(markdown, encoding="utf-8")
    Path("output/today.html").write_text(page, encoding="utf-8")
    Path("docs/index.html").write_text(page, encoding="utf-8")
    print("Generated mock pages: output/today.md, output/today.html, docs/index.html")


if __name__ == "__main__":
    main()
