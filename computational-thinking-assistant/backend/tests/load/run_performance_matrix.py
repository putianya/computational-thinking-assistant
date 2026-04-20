# -*- coding: utf-8 -*-
"""多场景矩阵压测：一次执行多个并发档位并生成对比图与总报告。"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent.parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from generate_charts import generate_all_charts
from run_performance_suite import (
    run_locust,
    start_mock_server,
    stop_process,
    wait_for_http_ready,
)


plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams.update({"font.size": 11})


DEFAULT_SCENARIOS = [
    {"name": "baseline", "users": 20, "spawn_rate": 5.0, "run_time": "30s"},
    {"name": "standard", "users": 50, "spawn_rate": 10.0, "run_time": "45s"},
    {"name": "stress", "users": 80, "spawn_rate": 15.0, "run_time": "60s"},
]


def parse_scenarios(raw):
    if not raw:
        return DEFAULT_SCENARIOS

    scenarios = []
    parts = [x.strip() for x in raw.split(",") if x.strip()]
    for item in parts:
        fields = [f.strip() for f in item.split(":")]
        if len(fields) != 4:
            raise ValueError(
                "场景参数格式错误，应为 name:users:spawn_rate:run_time，多个场景用英文逗号分隔。"
            )
        name, users, spawn_rate, run_time = fields
        if not name:
            raise ValueError("场景名称不能为空。")
        scenarios.append(
            {
                "name": name,
                "users": int(users),
                "spawn_rate": float(spawn_rate),
                "run_time": run_time,
            }
        )
    return scenarios


def _save_chart(fig, output_path):
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_matrix_latency(rows, output_dir):
    names = [x["name"] for x in rows]
    avg = [x["avg_ms"] for x in rows]
    p95 = [x["p95_ms"] for x in rows]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    bars1 = ax.bar(x - width / 2, avg, width, label="平均响应时间", color="#2A9D8F")
    bars2 = ax.bar(x + width / 2, p95, width, label="P95 响应时间", color="#E76F51")

    ax.set_title("图5-8 不同并发场景下响应时间对比")
    ax.set_ylabel("响应时间 (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend()
    ax.bar_label(bars1, padding=3, fmt="%.1f")
    ax.bar_label(bars2, padding=3, fmt="%.1f")

    out = output_dir / "fig5_8_matrix_latency.png"
    _save_chart(fig, out)
    return str(out)


def plot_matrix_throughput(rows, output_dir):
    names = [x["name"] for x in rows]
    rps = [x["rps"] for x in rows]

    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    bars = ax.bar(names, rps, color="#457B9D")

    ax.set_title("图5-9 不同并发场景下系统吞吐率对比")
    ax.set_ylabel("吞吐率 (Requests/s)")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.bar_label(bars, padding=3, fmt="%.2f")

    out = output_dir / "fig5_9_matrix_rps.png"
    _save_chart(fig, out)
    return str(out)


def plot_matrix_success_rate(rows, output_dir):
    names = [x["name"] for x in rows]
    success = [x["success_rate"] for x in rows]

    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    bars = ax.bar(names, success, color="#264653")

    ax.set_title("图5-10 不同并发场景下请求成功率对比")
    ax.set_ylabel("成功率 (%)")
    ax.set_ylim(95, 100.5)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.bar_label(bars, padding=3, fmt="%.2f%%")

    out = output_dir / "fig5_10_matrix_success_rate.png"
    _save_chart(fig, out)
    return str(out)


def write_matrix_report(rows, chart_paths, report_path, base_info):
    lines = []
    lines.append("# 性能测试矩阵报告（自动生成）")
    lines.append("")
    lines.append(f"- 生成时间：{base_info['generated_at']}")
    lines.append(f"- 目标地址：{base_info['host']}")
    lines.append("")
    lines.append("## 场景说明")
    lines.append("")
    lines.append("| 场景 | 并发用户 | 生成速率 | 持续时间 |")
    lines.append("|---|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['users']} | {row['spawn_rate']} | {row['run_time']} |"
        )

    lines.append("")
    lines.append("## 核心结果")
    lines.append("")
    lines.append("| 场景 | Locust退出码 | 总请求数 | 失败数 | 成功率 | 平均响应(ms) | P95(ms) | 吞吐(req/s) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            f"| {row['name']} | {row.get('locust_exit_code', 0)} | {row['request_count']} | {row['failure_count']} | "
            f"{row['success_rate']:.2f}% | {row['avg_ms']:.2f} | {row['p95_ms']:.2f} | {row['rps']:.2f} |"
        )

    lines.append("")
    lines.append("## 对比图")
    lines.append("")
    for key, path in chart_paths.items():
        rel = os.path.relpath(path, BACKEND_DIR).replace("\\", "/")
        lines.append(f"- {key}: {rel}")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="执行多场景性能压测并输出矩阵对比图")
    parser.add_argument("--host", default="http://127.0.0.1:5010", help="压测目标地址")
    parser.add_argument("--python", default=sys.executable, help="Python 可执行文件")
    parser.add_argument(
        "--scenarios",
        default="",
        help="自定义场景，格式为 name:users:spawn_rate:run_time，多个场景以英文逗号分隔",
    )
    parser.add_argument("--prefix", default="result_matrix", help="CSV 输出前缀")
    parser.add_argument(
        "--from-timestamp",
        default="",
        help="离线汇总模式：指定已有CSV时间戳，仅重建图表与报告，不重新发起压测",
    )
    parser.add_argument("--startup-timeout", type=int, default=40, help="后端启动等待秒数")
    parser.set_defaults(start_mock_server=True)
    parser.add_argument("--start-mock-server", dest="start_mock_server", action="store_true")
    parser.add_argument("--no-start-mock-server", dest="start_mock_server", action="store_false")

    args = parser.parse_args()
    scenarios = parse_scenarios(args.scenarios)

    ts = args.from_timestamp.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    matrix_dir = CURRENT_DIR / f"performance_matrix_{ts}"
    matrix_dir.mkdir(parents=True, exist_ok=True)

    process = None
    rows = []

    try:
        need_run_locust = not bool(args.from_timestamp.strip())

        if args.start_mock_server and need_run_locust:
            print("[1/4] 启动 mock 压测后端...")
            process = start_mock_server(args.python)
            health_url = f"{args.host.rstrip('/')}/api/test"
            if not wait_for_http_ready(health_url, timeout_seconds=args.startup_timeout):
                raise RuntimeError(f"后端启动超时，无法访问: {health_url}")
            print("后端已就绪。")

        if need_run_locust:
            print("[2/4] 执行矩阵压测场景...")
        else:
            print("[2/4] 离线汇总模式：读取已有CSV并重建图表...")

        for i, sc in enumerate(scenarios, start=1):
            print(
                f"  - 场景 {i}/{len(scenarios)}: {sc['name']} "
                f"(users={sc['users']}, spawn_rate={sc['spawn_rate']}, run_time={sc['run_time']})"
            )

            csv_prefix = CURRENT_DIR / f"{args.prefix}_{sc['name']}_{ts}"
            stats_csv = Path(f"{csv_prefix}_stats.csv")
            history_csv = Path(f"{csv_prefix}_stats_history.csv")

            locust_exit_code = 0
            if need_run_locust:
                try:
                    locust_exit_code = run_locust(
                        python_executable=args.python,
                        host=args.host,
                        users=sc["users"],
                        spawn_rate=sc["spawn_rate"],
                        run_time=sc["run_time"],
                        csv_prefix=csv_prefix,
                        locust_file=CURRENT_DIR / "locustfile.py",
                        check=True,
                    )
                except subprocess.CalledProcessError as exc:
                    locust_exit_code = exc.returncode
                    print(
                        f"  ! 场景 {sc['name']} Locust 退出码 {locust_exit_code}，"
                        "继续使用已生成CSV进行汇总。"
                    )

            if not stats_csv.exists():
                raise FileNotFoundError(f"未找到场景结果文件: {stats_csv}")

            scenario_dir = matrix_dir / sc["name"]
            scenario_dir.mkdir(parents=True, exist_ok=True)

            summary = generate_all_charts(
                stats_csv_path=str(stats_csv),
                history_csv_path=str(history_csv) if history_csv.exists() else None,
                output_dir=str(scenario_dir),
            )
            agg = summary["aggregated"]
            rows.append(
                {
                    "name": sc["name"],
                    "users": sc["users"],
                    "spawn_rate": sc["spawn_rate"],
                    "run_time": sc["run_time"],
                    "request_count": agg["request_count"],
                    "failure_count": agg["failure_count"],
                    "success_rate": agg["success_rate"],
                    "avg_ms": agg["avg_ms"],
                    "p95_ms": agg["p95_ms"],
                    "rps": agg["rps"],
                    "stats_csv": str(stats_csv),
                    "history_csv": str(history_csv) if history_csv.exists() else None,
                    "chart_dir": str(scenario_dir),
                    "locust_exit_code": locust_exit_code,
                }
            )

        print("[3/4] 生成矩阵对比图...")
        chart_paths = {
            "latency_matrix": plot_matrix_latency(rows, matrix_dir),
            "rps_matrix": plot_matrix_throughput(rows, matrix_dir),
            "success_rate_matrix": plot_matrix_success_rate(rows, matrix_dir),
        }

        matrix_json = matrix_dir / "performance_matrix_summary.json"
        matrix_report = matrix_dir / "performance_matrix_report.md"

        payload = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": args.host,
            "rows": rows,
            "charts": chart_paths,
        }
        matrix_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        print("[4/4] 输出矩阵报告...")
        write_matrix_report(
            rows=rows,
            chart_paths=chart_paths,
            report_path=matrix_report,
            base_info={
                "generated_at": payload["generated_at"],
                "host": args.host,
            },
        )

        print("矩阵压测完成。核心输出：")
        print(f"- 矩阵目录: {matrix_dir}")
        print(f"- 汇总JSON: {matrix_json}")
        print(f"- 报告MD: {matrix_report}")

    finally:
        stop_process(process)


if __name__ == "__main__":
    main()
