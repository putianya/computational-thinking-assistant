import argparse
import csv
import json
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams.update({"font.size": 11})


API_NAME_MAP = {
    "api_test": "/api/test",
    "auth_login": "/api/auth/login",
    "chat_stream": "/api/chat/stream",
    "code_analyze": "/api/code/analyze",
}


def _to_float(value, default=0.0):
    try:
        if value is None:
            return default
        value = str(value).strip()
        if not value or value.upper() == "N/A":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        if value is None:
            return default
        value = str(value).strip()
        if not value:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def load_stats(stats_csv_path):
    aggregated = None
    endpoints = []

    with open(stats_csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name") or "").strip()
            req_type = (row.get("Type") or "").strip()
            if not name:
                continue

            row_data = {
                "name": name,
                "display_name": API_NAME_MAP.get(name, name),
                "type": req_type,
                "request_count": _to_int(row.get("Request Count")),
                "failure_count": _to_int(row.get("Failure Count")),
                "median_ms": _to_float(row.get("Median Response Time")),
                "avg_ms": _to_float(row.get("Average Response Time")),
                "min_ms": _to_float(row.get("Min Response Time")),
                "max_ms": _to_float(row.get("Max Response Time")),
                "rps": _to_float(row.get("Requests/s")),
                "failures_per_s": _to_float(row.get("Failures/s")),
                "p95_ms": _to_float(row.get("95%")),
            }
            req = row_data["request_count"]
            fail = row_data["failure_count"]
            row_data["success_rate"] = ((req - fail) / req * 100.0) if req else 100.0

            if name == "Aggregated":
                aggregated = row_data
            elif req_type in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                endpoints.append(row_data)

    if aggregated is None:
        raise ValueError("在 stats CSV 中未找到 Aggregated 行，请检查 Locust 输出。")

    return aggregated, endpoints


def load_history(history_csv_path):
    if not history_csv_path or not os.path.exists(history_csv_path):
        return [], [], []

    timestamps = []
    rps_list = []
    p95_list = []

    with open(history_csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name") or "").strip()
            if name != "Aggregated":
                continue
            ts = _to_int(row.get("Timestamp"))
            if ts <= 0:
                continue
            timestamps.append(ts)
            rps_list.append(_to_float(row.get("Requests/s")))
            p95_list.append(_to_float(row.get("95%")))

    if not timestamps:
        return [], [], []

    start = timestamps[0]
    seconds = [ts - start for ts in timestamps]
    return seconds, rps_list, p95_list


def _ensure_output_dir(output_dir):
    os.makedirs(output_dir, exist_ok=True)


def plot_latency_comparison(endpoints, output_dir):
    _ensure_output_dir(output_dir)
    if not endpoints:
        return None

    business_endpoints = [e for e in endpoints if e["name"] != "api_test"] or endpoints
    business_endpoints = sorted(business_endpoints, key=lambda x: x["request_count"], reverse=True)
    selected = business_endpoints[:5]

    names = [e["display_name"] for e in selected]
    avg_values = [e["avg_ms"] for e in selected]
    p95_values = [e["p95_ms"] for e in selected]

    x = np.arange(len(names))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    bars1 = ax.bar(x - width / 2, avg_values, width, label="平均响应时间", color="#2A9D8F")
    bars2 = ax.bar(x + width / 2, p95_values, width, label="P95 响应时间", color="#E76F51")

    ax.set_ylabel("响应时间 (ms)")
    ax.set_title("图5-4 核心接口平均与P95响应时间对比")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=10)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend()
    ax.bar_label(bars1, padding=3, fmt="%.1f")
    ax.bar_label(bars2, padding=3, fmt="%.1f")

    out_path = os.path.join(output_dir, "fig5_4_latency_comparison.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_rps_comparison(endpoints, aggregated, output_dir):
    _ensure_output_dir(output_dir)
    if not endpoints:
        return None

    business_endpoints = [e for e in endpoints if e["name"] != "api_test"] or endpoints
    business_endpoints = sorted(business_endpoints, key=lambda x: x["rps"], reverse=False)

    names = [e["display_name"] for e in business_endpoints] + ["Aggregated"]
    values = [e["rps"] for e in business_endpoints] + [aggregated["rps"]]

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    bars = ax.barh(names, values, color=["#457B9D"] * (len(values) - 1) + ["#1D3557"])

    ax.set_xlabel("吞吐率 (Requests/s)")
    ax.set_title("图5-5 各接口与整体吞吐率对比")
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    ax.bar_label(bars, padding=3, fmt="%.2f")

    out_path = os.path.join(output_dir, "fig5_5_rps_comparison.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_history_trend(seconds, rps_list, p95_list, output_dir):
    _ensure_output_dir(output_dir)
    if not seconds:
        return None

    fig, ax1 = plt.subplots(figsize=(9.5, 5.2))
    line1 = ax1.plot(seconds, rps_list, color="#2A9D8F", linewidth=2.0, label="Requests/s")
    ax1.set_xlabel("测试时长 (s)")
    ax1.set_ylabel("吞吐率 (Requests/s)", color="#2A9D8F")
    ax1.tick_params(axis="y", labelcolor="#2A9D8F")
    ax1.grid(axis="both", linestyle="--", alpha=0.25)

    ax2 = ax1.twinx()
    line2 = ax2.plot(seconds, p95_list, color="#E76F51", linewidth=2.0, label="P95(ms)")
    ax2.set_ylabel("P95 响应时间 (ms)", color="#E76F51")
    ax2.tick_params(axis="y", labelcolor="#E76F51")

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left")
    plt.title("图5-6 压测过程中吞吐率与P95变化趋势")

    out_path = os.path.join(output_dir, "fig5_6_trend_rps_p95.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_success_rate(endpoints, aggregated, output_dir):
    _ensure_output_dir(output_dir)
    if not endpoints:
        return None

    business_endpoints = [e for e in endpoints if e["name"] != "api_test"] or endpoints
    names = [e["display_name"] for e in business_endpoints] + ["Aggregated"]
    rates = [e["success_rate"] for e in business_endpoints] + [aggregated["success_rate"]]

    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    bars = ax.bar(names, rates, color="#264653")
    ax.set_ylim(95, 100.5)
    ax.set_ylabel("成功率 (%)")
    ax.set_title("图5-7 关键接口请求成功率")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.bar_label(bars, padding=3, fmt="%.2f%%")

    out_path = os.path.join(output_dir, "fig5_7_success_rate.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def generate_all_charts(stats_csv_path, history_csv_path=None, output_dir="charts_output"):
    aggregated, endpoints = load_stats(stats_csv_path)
    seconds, rps_list, p95_list = load_history(history_csv_path)

    charts = {
        "latency": plot_latency_comparison(endpoints, output_dir),
        "rps": plot_rps_comparison(endpoints, aggregated, output_dir),
        "trend": plot_history_trend(seconds, rps_list, p95_list, output_dir),
        "success_rate": plot_success_rate(endpoints, aggregated, output_dir),
    }

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats_csv": os.path.abspath(stats_csv_path),
        "history_csv": os.path.abspath(history_csv_path) if history_csv_path else None,
        "aggregated": aggregated,
        "endpoints": endpoints,
        "charts": charts,
    }

    summary_path = os.path.join(output_dir, "performance_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


def main():
    parser = argparse.ArgumentParser(description="根据 Locust CSV 自动生成论文可用性能图表")
    parser.add_argument("--stats-csv", required=True, help="Locust *_stats.csv 文件路径")
    parser.add_argument("--history-csv", default=None, help="Locust *_stats_history.csv 文件路径")
    parser.add_argument("--output-dir", default="charts_output", help="图表输出目录")
    args = parser.parse_args()

    summary = generate_all_charts(
        stats_csv_path=args.stats_csv,
        history_csv_path=args.history_csv,
        output_dir=args.output_dir,
    )

    print("图表与汇总已生成：")
    for key, value in summary["charts"].items():
        if value:
            print(f"- {key}: {value}")
    print(f"- summary: {os.path.join(args.output_dir, 'performance_summary.json')}")


if __name__ == "__main__":
    main()