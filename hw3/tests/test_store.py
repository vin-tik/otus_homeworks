"""Store functions testing.
"""

import unittest
import store
import tarantool


class TarantoolStoreTest(unittest.TestCase):
    """Tarantool storage get and set functions tests.
    """

    def test_failed_get(self):
        '''Checks if store raises DatabaseError
        with getting random key.
        '''

        test_key = 'key'
        tarantool_storage = store.TarantoolStorage()
        storage = store.Store(tarantool_storage)
        with self.assertRaises(tarantool.DatabaseError()):
            storage.get(test_key)


    def test_none_from_cache(self):
        '''Checks if store returns None from cache
        with pushing random key.
        '''

        test_key, test_value = 'key', 'value'
        tarantool_storage = store.TarantoolStorage()
        storage = store.Store(tarantool_storage)
        self.assertEqual(storage.cache_get(test_key), None)
        self.assertEqual(storage.cache_set(test_key, test_value), None)


    def test_retries(self):
        '''Checks whether the function is
        reconnected when accessing the cache.
        '''

        tarantool_storage = store.TarantoolStorage()
        storage = store.Store(tarantool_storage)
        tarantool_retries = tarantool_storage.connection().reconnect_max_attempts
        
        self.assertEqual(tarantool_retries, storage.RETRIES)

if __name__ == "__main__":
    unittest.main()
