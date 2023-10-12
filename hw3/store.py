"""Store logic realization.
"""

import functools
import time
import random
import tarantool


def retry(retries=3):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for _ in retries:
                try:
                    return f(*args, **kwargs)
                except (tarantool.NetworkError,
                        ConnectionRefusedError):
                    random_sec = random.randint(2, 7)
                    time.sleep(random_sec)
        return wrapper
    return decorator


class TarantoolStorage:
    """Key-value storage based on Tarantool logic.
    """

    def __init__(self, host="localhost", port=8888, retries=3):
        self.host = host
        self.port = port
        self.retries = retries
        self.tsconnect = self.connect()


    def connection(self):
        '''Tarantool storage connection initialization.
        '''

        conn = tarantool.Connection(connect_now=False)
        conn.reconnect_max_attempts = self.retries
        return conn


    def connect(self):
        '''Run connection.
        '''

        self.connection().connect(self.host, self.port)


    def get(self, key):
        '''Try get value by key from the tarantool db.
        '''

        try:
            return self.tsconnect.select(key)
        except tarantool.DatabaseError:
            raise tarantool.DatabaseError(("No such index"))


    def set(self, key, value, sec):
        '''Try place data in the tarantool db.
        '''

        try:
            return self.tsconnect.insert((key, value, sec))
        except tarantool.DatabaseError:
            raise tarantool.DatabaseError(("Duplicate key exists in a unique index"))


class Store:
    """Main storage class.
    """

    RETRIES = 3

    def __init__(self, storage):
        self.storage = storage

    def get(self, key):
        '''Get value from db.
        '''

        return self.storage.get(key)

    @retry(RETRIES)
    def cache_get(self, key):
        '''Get value from cache.
        '''

        return self.storage.get(key)

    @retry(RETRIES)
    def cache_set(self, key, value, sec):
        '''Place data in the cache.
        '''

        return self.storage.set((key, value, sec))
