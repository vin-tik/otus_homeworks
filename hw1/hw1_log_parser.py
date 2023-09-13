#!/usr/bin/env python
# coding: utf-8

# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import datetime
import gzip
import itertools
import json
import logging
import os
import re

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

config_from_file = './config.json'

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as conf:
        config = json.load(conf)
    return config

def create_args_parser(config_from_file):
    parser = ArgumentParser()
    parser.add_argument('--config', help='config path', default=config_from_file)
    return parser

def does_dir_exists(dirpath):
    if not os.path.exists(dirpath):
        logging.info("directory doesn't exist")
        return False
    return True
    
def is_dir_empty(dirpath):
    if not os.listdir(dirpath):
        logging.info("directory is empty")
        return True
    return False

def check_dir(dirpath):
    if does_dir_exists(dirpath) and not is_dir_empty(dirpath):
        return True
    return False

def str_date(string):
    return datetime.datetime.strptime(string,
                                      '%Y%m%d'
                                      ).strftime('%Y%m%d')

def get_last_log(logdir):
    last_logdate = None
    pattern = re.compile('^nginx-access-ui.log-(\d{8})')
    if check_dir(logdir):    
        for file in os.listdir(logdir):
            matched = pattern.match(file)
            if matched:
                date_string = matched.groups()[0]
                log_date = str_date(date_string)
                if not last_logdate:
                    last_logdate = log_date
                if log_date >= last_logdate:
                    last_log = file
                    last_logdate = log_date
                    last_log_path = os.path.join(os.path.abspath(logdir), last_log)
            else:
                logging.debug("no ui log files")
        logging.info(f"last log file: {last_log}")
        return last_log_path, last_logdate
    else: 
        raise FileNotFoundError("there's no log file")

def median(numbers_list):
    sorted_numbers_list = sorted(numbers_list)
    length = len(numbers_list)
    middle = length // 2

    if length % 2 == 0:
        median = (sorted_numbers_list[middle - 1] + sorted_numbers_list[middle]) / 2
    else:
        median = sorted_numbers_list[middle]

    return median

def process_line(line):
    try: 
        url = line.split('"')[1].replace('GET ', '')
        http_idx = url.find(' HTT')
        url = url[:http_idx]
        reqtime = line.split(' ')[-1].replace('\n', '')
        return url, reqtime
    
    except IndexError:
        return None

def xreadlines(log_path, errors_threshold):
    if log_path.endswith(".gz"):
        log = gzip.open(log_path, 'rb')
    else:
        log = open(log_path)
    total = processed = errors = 0
    for line in log:
        parsed_line = process_line(line)
        total += 1
        if parsed_line:
            processed += 1
            yield parsed_line
        else:
            errors += 1
            if (errors / len(log)) >= errors_threshold:
                raise RuntimeError('wrong log format')
            else:
                continue
    log.close()

def url_timepoints_dict(log):
    pivot_dict = {}
    for url, time in log:
        if url not in pivot_dict:
            pivot_dict[url] = list()
        pivot_dict[url].append(float(time))
    return pivot_dict

def time_sum(url_time_dict):
    for url, timepoints in url_time_dict.items():
        yield url, sum(timepoints)
        
def sorted_reqs(url_time_dict, report_size):
    url_time_sum = dict(time_sum(url_time_dict))

    report = dict(
                  sorted(url_time_sum.items(),
                         key=lambda pair: pair[1],
                         reverse=True)
                    )
    
    report_sample = dict(
                         itertools.islice(
                                          report.items(), report_size
                                         )
                         )
    return report_sample

def dict_length(d):
    return len(list(d))

def all_reqs_timesum(utd):
    timesum = 0
    for _, timepoints in utd.items():
        timesum += sum(timepoints)
    return timesum

def round3(number):
    return round(number, ndigits=3)

def full_report(url_time_dict, max_time_sample, log):
    urls_table = []
    colnames = ['url', 'count', 'count_perc',
                'time_avg', 'time_max', 'time_med',
                'time_perc', 'time_sum']

    for url, url_timesum in max_time_sample.items():
            all_url_timepoints = url_time_dict.get(url)
            count = len(all_url_timepoints)
            count_perc = (count / len(log))*100
            time_avg = url_timesum / count
            time_max = max(all_url_timepoints)
            time_med = median(all_url_timepoints)
            time_perc = (url_timesum / all_reqs_timesum(url_time_dict))*100
            time_sum = url_timesum

            to_round = [count_perc, time_avg,
                        time_max, time_med, time_perc,
                        time_sum]
            
            stat_values = list(map(round3, to_round))
            url_row = list((url, count))
            url_row.extend(stat_values)
            url_table_row = dict(zip(colnames, url_row))
            urls_table.append(url_table_row)
    return urls_table

def errors_percent(errors_count, utd):
    all_urls_count = len(list(utd))
    return (errors_count / all_urls_count) * 100

def render_report(report_path, content):
    with open("report.html", "r") as report:
        page = report.read()
    page = page.replace("$table_json", str(content))
    with open(report_path, "w", encoding='utf-8') as report:
        report.write(page)
        logging.info('report is ready')

def main(config, errors_threshold):
    report_size = config['REPORT_SIZE']
    logdir = config['LOG_DIR']
    report_dir = config["REPORT_DIR"]

    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    last_log_path, logdate = get_last_log(logdir)
    logdate = f'{logdate[:4]}.{logdate[4:6]}.{logdate[6:]}'
    reportfname = (f'log_stats_report-{logdate}.html')
    reportpath = os.path.join(os.path.abspath(report_dir), reportfname)

    if not os.path.exists(reportpath):
        log = list(xreadlines(last_log_path, errors_threshold))
        logging.info('got log strings, start processing')
        utd = url_timepoints_dict(log)
        max_time_sample = sorted_reqs(utd, report_size)
        urls_report = full_report(utd, max_time_sample, log)
        
        logging.info('log processing completed, statistics calculated')
        logging.info('start report rendering')
        render_report(reportpath, urls_report)

    else:
        raise RuntimeError("you've got this log processing report yet!")

if __name__ == '__main__':
    
    logging.basicConfig(format=u'[%(asctime)s] %(levelname).1s %(message)s',
                        filename=None, datefmt='%Y.%m.%d %H:%M:%S',
                        level=logging.INFO)
    
    parser = create_args_parser(config_from_file)
    args = parser.parse_args()
    config = load_config(config_from_file)
    
    if args.config:
        external_config = load_config(args.config)
        logging.info('got your config')
        config.update(external_config)
    
    errors_threshold = config.get('ERR_THRESHOLD')
    if errors_threshold:
        main(config, errors_threshold)
    else:
        main(config, 30)
