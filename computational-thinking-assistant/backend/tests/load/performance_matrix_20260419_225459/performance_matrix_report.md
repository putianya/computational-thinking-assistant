# 性能测试矩阵报告（自动生成）

- 生成时间：2026-04-19 22:58:59
- 目标地址：http://127.0.0.1:5010

## 场景说明

| 场景     | 并发用户 | 生成速率 |     |
| -------- | -------: | -------: | --: |
| baseline |       20 |      5.0 | 15s |
| standard |       35 |      7.0 | 20s |
| stress   |       50 |     10.0 | 25s |

## 核心结果

| 场景     | Locust退出码 | 总请求数 | 失败数 |  成功率 | 平均响应(ms) | P95(ms) | 吞吐(req/s) |
| -------- | -----------: | -------: | -----: | ------: | -----------: | ------: | ----------: |
| baseline |            0 |      406 |      0 | 100.00% |        54.55 |  200.00 |       28.38 |
| standard |            0 |      792 |      0 | 100.00% |       138.87 |  680.00 |       43.72 |
| stress   |            0 |     1140 |      1 |  99.91% |       302.57 | 1000.00 |       49.32 |

## 对比图

- latency_matrix: tests/load/performance_matrix_20260419_225459/fig5_8_matrix_latency.png
- rps_matrix: tests/load/performance_matrix_20260419_225459/fig5_9_matrix_rps.png
- success_rate_matrix: tests/load/performance_matrix_20260419_225459/fig5_10_matrix_success_rate.png
