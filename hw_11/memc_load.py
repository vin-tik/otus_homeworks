#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import gzip
import sys
import glob
import logging
import collections
from optparse import OptionParser
# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2
# pip install python-memcached
import memcache
import threading
import Queue

NORMAL_ERR_RATE = 0.01
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])

config = {
    'MEMC_MAX_RETRIES': 1,
    'MEMC_TIMEOUT': 2,
    'MAX_JOB_QUEUE_SIZE': 5000,
    'MAX_RESULT_QUEUE_SIZE': 5000,
    'THREADS_COUNT': 4,
}

def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def insert_appsinstalled(memc_pool, memc_addr, appsinstalled, dry_run=False):
    ua = appsinstalled_pb2.UserApps()
    ua.lat = appsinstalled.lat
    ua.lon = appsinstalled.lon
    key = "%s:%s" % (appsinstalled.dev_type, appsinstalled.dev_id)
    ua.apps.extend(appsinstalled.apps)
    packed = ua.SerializeToString()
    try:
        if dry_run:
            logging.debug("%s - %s -> %s" % (memc_addr, key, str(ua).replace("\n", " ")))
        else:
            try:
                memc = memc_pool.get(timeout=0.1)
            except Queue.Empty:
                memc = memcache.Client([memc_addr], socket_timeout=config['MEMC_TIMEOUT'])
            is_ok = False
            max_retries = config['MEMC_MAX_RETRIES']
            for _ in range(max_retries):
                is_ok = memc.set(key, packed)
                if is_ok:
                    break
            memc_pool.put(memc)
            return is_ok
    except Exception as e:
        logging.exception("Cannot write to memc %s: %s" % (memc_addr, e))
        return False
    return True


def parse_appsinstalled(line):
    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isidigit()]
        logging.info("Not all user apps are digits: `%s`" % line)
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)
    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def get_logfile_size(fn):
    with gzip.open(fn) as fd:
        logsize = len(fd)
    return logsize


def logfile_to_queue(fn, queue):
    with gzip.open(fn) as fd:
        for container in range(0, len(fd), config['MAX_JOB_QUEUE_SIZE']):
            queue.put([container])


def log2memc(queue, result_q, options):
    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }

    processed = errors = 0

    while True:
        try:
            lines = queue.get()
        except Queue.Empty:
            result_q.put((processed, errors))

        else:
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                appsinstalled = parse_appsinstalled(line)
                if not appsinstalled:
                    errors += 1
                    continue
                memc_addr = device_memc.get(appsinstalled.dev_type)
                if not memc_addr:
                    errors += 1
                    logging.error("Unknown device type: %s" % appsinstalled.dev_type)
                    continue
                ok = insert_appsinstalled(memc_addr, appsinstalled, options.dry)
                if ok:
                    processed += 1
                else:
                    errors += 1
                if not processed:
                    continue

            result_q.put((processed, errors))
            queue.task_done()


def threaded_log_processing(fn, options):
    processed = errors = 0

    addition_threads = []
    loglines_queue = Queue.Queue()
    processing_report_queue = Queue.Queue()
    threads_count = get_logfile_size(fn) // config['MAX_JOB_QUEUE_SIZE']

    logging.info('Processing %s' % fn)

    # создаем и запускаем threads, которые будут добавлять в очередь
    # по f'{config['MAX_JOB_QUEUE_SIZE']}' строк из лога
    for _ in range(threads_count):
        addition_thread = threading.Thread(target=logfile_to_queue,
                                             args=(loglines_queue,))
        addition_thread.daemon = True
        addition_threads.append(addition_thread)

    for add_thread in addition_threads:
        add_thread.start()

    # создаем и запускаем threads, которые запускают обработку частей лога из loglines_queue
    proc_threads = []
    for _ in range(threads_count):
        proc_thread = threading.Thread(target=log2memc, args=(loglines_queue,
                                                                  processing_report_queue,
                                                                  options,))
        proc_thread.daemon = True
        proc_threads.append(proc_thread)

    for p_thread in proc_threads:
        p_thread.start()

    for add_thread in addition_threads:
        if add_thread.is_alive():
            add_thread.join()

    while not processing_report_queue.empty():
        processed_per_thread, errors_per_thread = processing_report_queue.get()
        processed += processed_per_thread
        errors += errors_per_thread

    if processed:
        err_rate = float(errors) / processed
        if err_rate < NORMAL_ERR_RATE:
            logging.info("Acceptable error rate (%s). Successfull load" % err_rate)
        else:
            logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))
        dot_rename(fn)
    else: dot_rename(fn)


def main(options):
    for fn in glob.iglob(options.pattern):
        threaded_log_processing(fn, options)


def prototest():
    sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        ua = appsinstalled_pb2.UserApps()
        ua.lat = lat
        ua.lon = lon
        ua.apps.extend(apps)
        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO if not opts.dry else logging.DEBUG,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    if opts.test:
        prototest()
        sys.exit(0)

    logging.info("Memc loader started with options: %s" % opts)
    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
