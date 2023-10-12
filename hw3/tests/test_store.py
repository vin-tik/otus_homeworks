"""Store functions testing.
"""

import unittest
from unittest.mock import Mock
import store
import tarantool


class TarantoolStoreTest(unittest.TestCase):
    """Tarantool storage get and set functions tests.
    """

    def test_failed_get(self):
        '''Checks if store raises DatabaseError
        with getting random key.
        '''

        tarantool_storage = store.TarantoolStorage()
        storage = store.Store(tarantool_storage)
        with self.assertRaises(tarantool.DatabaseError()):
            storage.get("key")


    def test_none_from_cache(self):
        '''Checks if store returns None from cache
        with pushing random key.
        '''

        tarantool_storage = store.TarantoolStorage()
        storage = store.Store(tarantool_storage)
        self.assertEqual(storage.cache_get("key"), None)
        self.assertEqual(storage.cache_set("key", "value"), None)


    def test_retries(self):
        '''Сhecks whether the function is
        reconnected when accessing the cache.
        '''

        tarantool_storage = store.TarantoolStorage()
        tarantool_storage.get = Mock(side_effect=tarantool.DatabaseError())
        tarantool_storage.set = Mock(side_effect=tarantool.DatabaseError())

        storage = store.Store(tarantool_storage)
        self.assertEqual(tarantool_storage.connection().reconnect_max_attempts, storage.RETRIES)

if __name__ == "__main__":
    unittest.main()
