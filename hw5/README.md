# Веб-сервер на локальном хосте
> При запуске можно задать аргументы в следующем порядке:
- --host - хост (по умолчанию 'localhost'), str
- -p - порт (по умолчанию 8080), int
- -w - количество worker'ов (по умолчанию 1), int
- -r - путь к корневой папке (по умолчанию текущая папка), str/path

## Нагрузочное тестирование ApacheBenchmark

```
$ ab -n 50000 -c 100 -r http://localhost:8080/
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   44.204 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      900000 bytes
HTML transferred:       0 bytes
Requests per second:    1131.13 [#/sec] (mean)
Time per request:       88.407 [ms] (mean)
Time per request:       0.884 [ms] (mean, across all concurrent requests)
Transfer rate:          19.88 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   1.1      0      16
Processing:     0    1   1.6      0      16
Waiting:        0    0   1.2      0      16
Total:          0    1   1.9      0      17

Percentage of the requests served within a certain time (ms)
  50%      0
  66%      0
  75%      0
  80%      1
  90%      3
  95%      5
  98%      7
  99%      9
 100%     17 (longest request)
 ```
