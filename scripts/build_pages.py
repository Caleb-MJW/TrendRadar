import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ_NAME = "Asia/Shanghai"
MOCK_NOTICE = "当前为模拟数据，仅用于测试页面链路，不代表真实热点，不建议作为素材参考。"
REAL_NOTICE = "当前为真实热榜数据，来源于平台公开热门榜单。"


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
            "mode": "real",
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
        official_links = []
        if entry.get("source_url"):
            official_links.append(f"[查看原文]({entry['source_url']})")
        if entry.get("board_item_url"):
            official_links.append(f"[查看榜单条目]({entry['board_item_url']})")
        if entry.get("board_url"):
            official_links.append(f"[查看热榜页面]({entry['board_url']})")
        official_text = " ".join(official_links) if official_links else "暂无正式出处链接。"
        lines.extend(
            [
                f"{index}. **{entry['original_title']}**",
                f"   - 来源平台: {entry['source_platform']} | 榜单名称: {entry.get('board_name') or entry['source_platform']} | 榜单排名: {entry['source_rank']} | 抓取时间: {entry.get('crawl_time') or '未知'}",
                f"   - 正式来源: {official_text}",
                f"   - 数据标记: {entry.get('source_origin_type', 'unknown')} | 参考有效性: {entry.get('is_reference_valid', False)}",
                f"   - 热点摘要: {entry['hotspot_summary']}",
                f"   - 为什么值得看: {entry['why_worth_attention']}",
                f"   - 话题性/趣味点: {entry['interest_point']}",
                f"   - 可轻度关联方向: {'、'.join(entry['weak_connection_directions'])}",
                f"   - 灵感提示: {'；'.join(entry['inspiration_tips'])}",
                f"   - 素材用途: {entry['material_usage']} | 推荐等级: {entry['recommend_level']} | 总分: {entry['total_score']}",
                f"   - 风险提醒: {entry['risk_note']}",
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
        f"- 当前模式: {analysis.get('mode', 'real')}",
        f"- 重要提示: {REAL_NOTICE if analysis.get('mode', 'real') == 'real' else MOCK_NOTICE}",
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
                f"- {source['platform']}: {source['status']}，抓取 {source.get('fetched_count', 0)} 条，原文链接 {source.get('with_source_url_count', 0)} 条，榜单条目链接 {source.get('with_board_item_url_count', 0)} 条，热榜页面链接 {source.get('with_board_url_count', 0)} 条"
            )
    else:
        lines.append("- 暂无健康状态数据。")
    lines.append("")
    return "\n".join(lines)


def render_source_links(entry: dict) -> str:
    links = []
    if entry.get("source_url"):
        links.append(
            f'<a class="source-button" href="{html.escape(entry["source_url"])}" target="_blank" rel="noopener noreferrer">查看原文</a>'
        )
    if entry.get("board_item_url"):
        links.append(
            f'<a class="source-button" href="{html.escape(entry["board_item_url"])}" target="_blank" rel="noopener noreferrer">查看榜单条目</a>'
        )
    if entry.get("board_url"):
        links.append(
            f'<a class="source-button" href="{html.escape(entry["board_url"])}" target="_blank" rel="noopener noreferrer">查看热榜页面</a>'
        )
    official = "".join(links) if links else '<span class="source-fallback">暂无正式出处，不进入素材参考。</span>'
    return f'<div class="source-block"><strong>正式来源：</strong><div class="source-actions">{official}</div></div>'


def render_tips(tips: list[str]) -> str:
    if not tips:
        return "<li>暂无灵感提示。</li>"
    return "".join(f"<li>{html.escape(tip)}</li>" for tip in tips)


def render_cards(entries: list[dict]) -> str:
    if not entries:
        return "<p>暂无数据。</p>"
    cards = []
    for index, entry in enumerate(entries, 1):
        title = html.escape(entry["original_title"])
        summary = html.escape(entry["hotspot_summary"])
        why = html.escape(entry["why_worth_attention"])
        interest = html.escape(entry["interest_point"])
        directions = "、".join(html.escape(item) for item in entry["weak_connection_directions"])
        mock_badge = ""
        if entry.get("source_origin_type") == "mock_hotlist":
            mock_badge = '<p class="mock-badge">模拟热榜条目｜仅测试展示，不作为真实素材来源</p>'
        cards.append(
            f"""
            <article class="item">
              <div class="rank">{index}</div>
              <div>
                <h3>{title}</h3>
                <p class="meta">来源平台：{html.escape(entry['source_platform'])} · 榜单名称：{html.escape(entry.get('board_name') or entry['source_platform'])} · 榜单排名：{entry['source_rank']} · 抓取时间：{html.escape(str(entry.get('crawl_time') or '未知'))} · 来源等级：{html.escape(entry.get('source_level', 'no_link'))}</p>
                {mock_badge}
                {render_source_links(entry)}
                <p><strong>热点摘要：</strong>{summary}</p>
                <p><strong>为什么值得看：</strong>{why}</p>
                <p><strong>话题性/趣味点：</strong>{interest}</p>
                <p><strong>可轻度关联方向：</strong>{directions}</p>
                <div class="tips"><strong>灵感提示：</strong><ul>{render_tips(entry.get('inspiration_tips', []))}</ul></div>
                <p class="meta">素材用途：{html.escape(entry['material_usage'])} · 推荐等级：{html.escape(entry['recommend_level'])} · 总分：{entry['total_score']}</p>
                <p class="risk">风险提醒：{html.escape(entry['risk_note'])}</p>
              </div>
            </article>
            """
        )
    return "\n".join(cards)


def render_html(analysis: dict, health: dict, generated_at: str) -> str:
    overview = analysis.get("today_overview", {})
    mode = analysis.get("mode", "real")
    notice = REAL_NOTICE if mode == "real" else MOCK_NOTICE
    health_rows = "\n".join(
        f"<tr><td>{html.escape(source['platform'])}</td><td>{html.escape(source['status'])}</td><td>{source.get('fetched_count', 0)}</td><td>{source.get('with_source_url_count', 0)}</td><td>{source.get('with_board_item_url_count', 0)}</td><td>{source.get('with_board_url_count', 0)}</td><td>{html.escape(str(source.get('source_origin_type', '')))}</td><td>{html.escape(str(source.get('error') or ''))}</td></tr>"
        for source in health.get("sources", [])
    )
    if not health_rows:
        health_rows = '<tr><td colspan="8">暂无健康状态数据。</td></tr>'

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
    .notice {{ margin-top: 12px; padding: 12px 14px; border: 1px solid #d6b25e; border-radius: 6px; background: #fff8e5; color: #5f4700; font-weight: 600; }}
    .mock-badge {{ display: inline-block; margin: 6px 0 10px; padding: 5px 8px; border-radius: 6px; background: #fff8e5; color: #5f4700; font-size: 14px; font-weight: 600; }}
    .overview {{ font-size: 17px; max-width: 880px; }}
    .item {{ display: grid; grid-template-columns: 42px 1fr; gap: 14px; padding: 16px 0; border-top: 1px solid #e4e7eb; }}
    .rank {{ width: 32px; height: 32px; border-radius: 6px; background: #1f2933; color: white; display: grid; place-items: center; font-weight: 700; }}
    .source-actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 12px; }}
    .source-block {{ display: grid; gap: 8px; margin: 10px 0 14px; padding: 10px 12px; background: #ffffff; border: 1px solid #e4e7eb; border-radius: 6px; }}
    .source-button {{ display: inline-flex; align-items: center; min-height: 32px; padding: 0 10px; border: 1px solid #c7d0d9; border-radius: 6px; color: #1f2933; background: #ffffff; text-decoration: none; font-size: 14px; }}
    .source-button:hover {{ background: #eef2f6; }}
    .source-fallback, .risk {{ color: #6b7280; font-size: 14px; }}
    .tips ul {{ margin-top: 8px; padding-left: 20px; }}
    .tips li {{ margin: 4px 0; line-height: 1.55; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ padding: 10px 12px; border: 1px solid #e4e7eb; text-align: left; }}
    th {{ background: #eef2f6; }}
  </style>
</head>
<body>
  <header>
    <main>
      <h1>今日热点灵感雷达</h1>
      <p class="mode">生成时间：{html.escape(generated_at)} · 当前模式：{html.escape(mode)}</p>
      <p class="notice">{notice}</p>
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
      <thead><tr><th>平台</th><th>状态</th><th>抓取数</th><th>原文链接数</th><th>榜单条目数</th><th>热榜页面数</th><th>来源类型</th><th>错误</th></tr></thead>
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
    print(f"Generated {analysis.get('mode', 'real')} pages: output/today.md, output/today.html, docs/index.html")


if __name__ == "__main__":
    main()
