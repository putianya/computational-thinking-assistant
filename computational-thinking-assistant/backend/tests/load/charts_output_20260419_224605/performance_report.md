# 性能测试报告（自动生成）

- 生成时间：2026-04-19 22:46:42
- 目标地址：http://127.0.0.1:5010
- 并发用户：20
- 生成速率：5.0
- 持续时间：30s

## 整体指标

- 总请求数：848
- 失败请求数：0
- 成功率：100.00%
- 平均响应时间：51.32 ms
- P95 响应时间：200.00 ms
- 吞吐率：30.10 req/s

## 分接口指标

| 接口 | 请求数 | 失败数 | 成功率 | 平均响应(ms) | P95(ms) | 吞吐(req/s) |
|---|---:|---:|---:|---:|---:|---:|
| /api/test | 206 | 0 | 100.00% | 6.24 | 11.00 | 7.31 |
| /api/auth/login | 20 | 0 | 100.00% | 231.79 | 420.00 | 0.71 |
| /api/chat/stream | 328 | 0 | 100.00% | 70.94 | 220.00 | 11.64 |
| /api/code/analyze | 294 | 0 | 100.00% | 48.74 | 150.00 | 10.43 |

## 图表文件

- latency: tests/load/charts_output_20260419_224605/fig5_4_latency_comparison.png
- rps: tests/load/charts_output_20260419_224605/fig5_5_rps_comparison.png
- trend: tests/load/charts_output_20260419_224605/fig5_6_trend_rps_p95.png
- success_rate: tests/load/charts_output_20260419_224605/fig5_7_success_rate.png