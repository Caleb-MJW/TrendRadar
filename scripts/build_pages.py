from datetime import datetime
from zoneinfo import ZoneInfo


SCRIPT_ROLE = "负责生成 output/today.md、output/today.html、docs/index.html"


def shanghai_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def main() -> None:
    now = shanghai_now()
    print("TrendRadar placeholder script: build_pages.py")
    print(f"职责: {SCRIPT_ROLE}")
    print(f"当前北京时间: {now:%Y-%m-%d %H:%M:%S %Z}")
    print("未来输出路径: output/today.md, output/today.html, docs/index.html")
    print("当前状态: 第一阶段占位，不生成真实热点页面。")


if __name__ == "__main__":
    main()
