from datetime import datetime
from zoneinfo import ZoneInfo


SCRIPT_ROLE = "负责把当天多个快照合并为热点簇 data/clusters/YYYY-MM-DD.json"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def main() -> None:
    now = shanghai_now()
    cluster_path = f"data/clusters/{now:%Y-%m-%d}.json"
    print("TrendRadar placeholder script: merge_clusters.py")
    print(f"职责: {SCRIPT_ROLE}")
    print(f"当前北京时间: {now:%Y-%m-%d %H:%M:%S %Z}")
    print(f"未来输出路径: {cluster_path}")
    print("当前状态: 第一阶段占位，不合并真实快照。")


if __name__ == "__main__":
    main()
