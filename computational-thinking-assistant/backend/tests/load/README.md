# 压测执行说明（Locust）

## 1) 启动压测专用后端

在 backend 目录运行：

```powershell
C:/Users/30485/anaconda3/python.exe tests/load/mock_backend_server.py
```

服务监听：`http://127.0.0.1:5010`

## 2) 执行并发压测（无 UI）

```powershell
C:/Users/30485/anaconda3/python.exe -m locust -f tests/load/locustfile.py --host http://127.0.0.1:5010 --users 50 --spawn-rate 10 --run-time 1m --headless --csv tests/load/result
```

输出文件：

- `tests/load/result_stats.csv`
- `tests/load/result_failures.csv`
- `tests/load/result_exceptions.csv`

## 3) 关键指标口径

- 平均响应时间：`Average Response Time`
- P95 响应时间：`95%`
- 请求成功率：`(Total Requests - # Fails) / Total Requests`
- 吞吐率：`Requests/s`

## 4) 一键执行（自动压测 + 自动出图 + 自动报告）

在 backend 目录运行：

```powershell
C:/Users/30485/anaconda3/python.exe tests/load/run_performance_suite.py --users 50 --spawn-rate 10 --run-time 1m
```

执行完成后将自动生成：

- 原始 CSV：`tests/load/result_auto_时间戳_stats.csv`
- 历史曲线 CSV：`tests/load/result_auto_时间戳_stats_history.csv`
- 图表目录：`tests/load/charts_output_时间戳/`
- 摘要报告：`tests/load/charts_output_时间戳/performance_report.md`
- 结构化汇总：`tests/load/charts_output_时间戳/performance_summary.json`

> 若压测目标不是本机 mock 服务，可追加 `--no-start-mock-server --host http://目标地址`。

## 5) 多场景矩阵压测（推荐用于论文性能章节）

该模式会依次执行多个并发场景（默认：baseline / standard / stress），并自动生成横向对比图与总报告。

在 backend 目录运行：

```powershell
C:/Users/30485/anaconda3/python.exe tests/load/run_performance_matrix.py
```

默认场景参数：

- baseline：`20` 用户，`5` 用户/秒，`30s`
- standard：`50` 用户，`10` 用户/秒，`45s`
- stress：`80` 用户，`15` 用户/秒，`60s`

可自定义场景，例如：

```powershell
C:/Users/30485/anaconda3/python.exe tests/load/run_performance_matrix.py --scenarios "baseline:30:6:30s,standard:60:12:45s,stress:100:20:60s"
```

输出内容：

- 矩阵目录：`tests/load/performance_matrix_时间戳/`
- 场景子目录：每个场景单独生成原始图表与汇总 JSON
- 矩阵对比图：
  - `fig5_8_matrix_latency.png`
  - `fig5_9_matrix_rps.png`
  - `fig5_10_matrix_success_rate.png`
- 总报告：`performance_matrix_report.md`
- 总汇总：`performance_matrix_summary.json`
