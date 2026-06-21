import unittest

from bot_test_harness import (
    MemoryStorageStub,
    RedisStorageStub,
    import_fresh,
    install_dependency_stubs,
)


class MainStorageTests(unittest.TestCase):
    def setUp(self):
        install_dependency_stubs()
        self.main = import_fresh('main')

    def test_build_fsm_storage_uses_redis_by_default(self):
        storage = self.main.build_fsm_storage()

        self.assertIsInstance(storage, RedisStorageStub)
        self.assertEqual(storage.redis.kwargs['db'], 2)
        self.assertEqual(storage.key_builder.prefix, 'doverabot:fsm')

    def test_build_fsm_storage_can_use_memory_for_local_override(self):
        self.main.settings.BOT_FSM_STORAGE = 'memory'

        self.assertIsInstance(self.main.build_fsm_storage(), MemoryStorageStub)

if __name__ == '__main__':
    unittest.main()
