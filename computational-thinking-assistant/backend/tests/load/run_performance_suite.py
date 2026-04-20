# -*- coding: utf-8 -*-
"""一键执行性能测试：启动压测后端、运行 Locust、自动生成汇总与图表。"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent.parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from generate_charts import generate_all_charts


def wait_for_http_ready(url, timeout_seconds=40):
    start = time.time()
    while time.time() - start <= timeout_seconds:
        try:
            with urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 500:
                    return True
        except URLError:
            pass
        except Exception:
            pass
        time.sleep(0.8)
    return False


def start_mock_server(python_executable):
    cmd = [python_executable, str(CURRENT_DIR / "mock_backend_server.py")]
    process = subprocess.Popen(
        cmd,
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process


def stop_process(process):
    if process is None:
        return
    try:
        process.terminate()
        process.wait(timeout=8)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def run_locust(python_executable, host, users, spawn_rate, run_time, csv_prefix, locust_file, check=True):
    cmd = [
        python_executable,
        "-m",
        "locust",
        "-f",
        str(locust_file),
        "--host",
        host,
        "--users",
        str(users),
        "--spawn-rate",
        str(spawn_rate),
        "--run-time",
        run_time,
        "--headless",
        "--only-summary",
        "--csv",
        str(csv_prefix),
    ]
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR), check=check)
    return result.returncode


def write_markdown_report(summary, report_path, config):
    aggregated = summary["aggregated"]
    endpoints = summary["endpoints"]
    charts = summary["charts"]

    lines = []
    lines.append("# 性能测试报告（自动生成）")
    lines.append("")
    lines.append(f"- 生成时间：{summary['generated_at']}")
    lines.append(f"- 目标地址：{config['host']}")
    lines.append(f"- 并发用户：{config['users']}")
    lines.append(f"- 生成速率：{config['spawn_rate']}")
    lines.append(f"- 持续时间：{config['run_time']}")
    lines.append("")
    lines.append("## 整体指标")
    lines.append("")
    lines.append(f"- 总请求数：{aggregated['request_count']}")
    lines.append(f"- 失败请求数：{aggregated['failure_count']}")
    lines.append(f"- 成功率：{aggregated['success_rate']:.2f}%")
    lines.append(f"- 平均响应时间：{aggregated['avg_ms']:.2f} ms")
    lines.append(f"- P95 响应时间：{aggregated['p95_ms']:.2f} ms")
    lines.append(f"- 吞吐率：{aggregated['rps']:.2f} req/s")
    lines.append("")
    lines.append("## 分接口指标")
    lines.append("")
    lines.append("| 接口 | 请求数 | 失败数 | 成功率 | 平均响应(ms) | P95(ms) | 吞吐(req/s) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for item in endpoints:
        lines.append(
            f"| {item['display_name']} | {item['request_count']} | {item['failure_count']} | "
            f"{item['success_rate']:.2f}% | {item['avg_ms']:.2f} | {item['p95_ms']:.2f} | {item['rps']:.2f} |"
        )

    lines.append("")
    lines.append("## 图表文件")
    lines.append("")
    for key, path in charts.items():
        if path:
            rel = os.path.relpath(path, BACKEND_DIR).replace("\\", "/")
            lines.append(f"- {key}: {rel}")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="运行后端性能测试并自动生成图表与报告")
    parser.add_argument("--host", default="http://127.0.0.1:5010", help="压测目标地址")
    parser.add_argument("--users", type=int, default=50, help="并发用户数")
    parser.add_argument("--spawn-rate", type=float, default=10.0, help="每秒新增用户数")
    parser.add_argument("--run-time", default="1m", help="压测持续时间，例如 45s、2m")
    parser.add_argument("--python", default=sys.executable, help="用于执行脚本的 Python 可执行文件")
    parser.add_argument("--prefix", default="result_auto", help="输出 CSV 前缀")
    parser.add_argument("--output-dir", default="charts_output", help="图表输出目录")
    parser.add_argument("--startup-timeout", type=int, default=40, help="后端启动等待秒数")
    parser.set_defaults(start_mock_server=True)
    parser.add_argument("--start-mock-server", dest="start_mock_server", action="store_true", help="自动启动 mock 压测后端")
    parser.add_argument("--no-start-mock-server", dest="start_mock_server", action="store_false", help="不自动启动后端，直接压测 host")

    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_prefix = CURRENT_DIR / f"{args.prefix}_{timestamp}"
    stats_csv = Path(f"{csv_prefix}_stats.csv")
    history_csv = Path(f"{csv_prefix}_stats_history.csv")

    process = None
    try:
        if args.start_mock_server:
            print("[1/4] 启动 mock 压测后端...")
            process = start_mock_server(args.python)
            health_url = f"{args.host.rstrip('/')}/api/test"
            if not wait_for_http_ready(health_url, timeout_seconds=args.startup_timeout):
                raise RuntimeError(f"后端启动超时，无法访问: {health_url}")
            print("后端已就绪。")

        print("[2/4] 执行 Locust 压测...")
        run_locust(
            python_executable=args.python,
            host=args.host,
            users=args.users,
            spawn_rate=args.spawn_rate,
            run_time=args.run_time,
            csv_prefix=csv_prefix,
            locust_file=CURRENT_DIR / "locustfile.py",
        )

        if not stats_csv.exists():
            raise FileNotFoundError(f"未找到压测结果文件: {stats_csv}")

        print("[3/4] 读取 CSV 并生成图表...")
        chart_dir = CURRENT_DIR / f"{args.output_dir}_{timestamp}"
        summary = generate_all_charts(
            stats_csv_path=str(stats_csv),
            history_csv_path=str(history_csv) if history_csv.exists() else None,
            output_dir=str(chart_dir),
        )

        if summary["aggregated"]["request_count"] <= 0:
            raise RuntimeError("Locust 本次执行未产生有效请求，请检查目标服务与压测参数。")

        summary_json = chart_dir / "performance_summary.json"
        report_md = chart_dir / "performance_report.md"

        print("[4/4] 输出结构化报告...")
        write_markdown_report(
            summary=summary,
            report_path=report_md,
            config={
                "host": args.host,
                "users": args.users,
                "spawn_rate": args.spawn_rate,
                "run_time": args.run_time,
            },
        )

        result = {
            "stats_csv": str(stats_csv),
            "history_csv": str(history_csv) if history_csv.exists() else None,
            "chart_dir": str(chart_dir),
            "summary_json": str(summary_json),
            "report_md": str(report_md),
        }
        out_json = chart_dir / "run_output.json"
        out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        print("性能测试完成。核心输出：")
        print(f"- stats: {stats_csv}")
        if history_csv.exists():
            print(f"- history: {history_csv}")
        print(f"- charts: {chart_dir}")
        print(f"- report: {report_md}")
        print(f"- run output: {out_json}")

    finally:
        stop_process(process)


if __name__ == "__main__":
    main()
