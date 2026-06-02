from datetime import datetime
from zoneinfo import ZoneInfo


SCRIPT_ROLE = "负责抓取热点并保存 data/snapshots/YYYY-MM-DD/HHMM.json"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def main() -> None:
    now = shanghai_now()
    snapshot_path = f"data/snapshots/{now:%Y-%m-%d}/{now:%H%M}.json"
    print("TrendRadar placeholder script: fetch_hotspots.py")
    print(f"职责: {SCRIPT_ROLE}")
    print(f"当前北京时间: {now:%Y-%m-%d %H:%M:%S %Z}")
    print(f"未来输出路径: {snapshot_path}")
    print("当前状态: 第一阶段占位，不接入真实抓取。")


if __name__ == "__main__":
    main()
