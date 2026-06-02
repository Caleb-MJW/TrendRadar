from datetime import datetime
from zoneinfo import ZoneInfo


SCRIPT_ROLE = "负责生成每日归档 data/daily/YYYY-MM-DD_final.json 和 output/archive/YYYY-MM-DD.html"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def main() -> None:
    now = shanghai_now()
    final_json_path = f"data/daily/{now:%Y-%m-%d}_final.json"
    archive_html_path = f"output/archive/{now:%Y-%m-%d}.html"
    print("TrendRadar placeholder script: archive_daily.py")
    print(f"职责: {SCRIPT_ROLE}")
    print(f"当前北京时间: {now:%Y-%m-%d %H:%M:%S %Z}")
    print(f"未来输出路径: {final_json_path}, {archive_html_path}")
    print("当前状态: 第一阶段占位，不生成真实每日归档。")


if __name__ == "__main__":
    main()
