# gzip/plain log parser
> Парсер собирает статистику по URL и рендерит отчет.
В отчет попадают URL'ы с наибольшим суммарным временем обработки.

## Usage example

>> python hw1_log_parser
[2023.09.09 22:04:14] I last log file: nginx-access-ui.log-20170630
[2023.09.09 22:04:19] I got log strings, start processing
...

По умолчанию скрипт ищет логи в папке 'log', сохраняет отчет в папкe 'reports'.
Отчет содержит первые 1000 URL, отсортированные по убыванию суммарного времени.

Настройки, отличающиеся от дефолтных, принимаются через --config:

>> python hw1_log_parser --config
[2023.09.09 22:04:14] I got your config
[2023.09.09 22:04:14] I last log file: nginx-access-ui.log-20170630
[2023.09.09 22:04:19] I got log strings, start processing
...

В --config передается json со структурой:

    {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
    "ERR_THRESHOLD": 30
    },

где 'ERR_THRESHOLD' - доля ошибочно обработанных строк лога, в процентах.
При превышении данного порога скрипт останавливается и не формирует отчет.

