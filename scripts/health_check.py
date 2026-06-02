from datetime import datetime
from zoneinfo import ZoneInfo


SCRIPT_ROLE = "负责生成信息源健康状态 data/health/YYYY-MM-DD_HHMM.json"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def main() -> None:
    now = shanghai_now()
    health_path = f"data/health/{now:%Y-%m-%d_%H%M}.json"
    print("TrendRadar placeholder script: health_check.py")
    print(f"职责: {SCRIPT_ROLE}")
    print(f"当前北京时间: {now:%Y-%m-%d %H:%M:%S %Z}")
    print(f"未来输出路径: {health_path}")
    print("当前状态: 第一阶段占位，不检测真实信息源。")


if __name__ == "__main__":
    main()
