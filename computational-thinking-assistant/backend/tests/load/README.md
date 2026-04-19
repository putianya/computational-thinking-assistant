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
