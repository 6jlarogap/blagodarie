import sys
import types
import unittest
from unittest import mock

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


class MainLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_preserves_updates_and_closes_api_session_when_polling_stops(self):
        install_dependency_stubs()
        main = import_fresh('main')
        for name in (
            'handler_bot', 'handler_callbacks', 'handler_group', 'handler_offer',
            'handler_rental', 'handler_sympas', 'handler_relatives',
        ):
            module = types.ModuleType(name)
            module.router = object()
            sys.modules[name] = module

        class Session:
            closed = False

            async def close(self):
                self.closed = True

        class RuntimeBot:
            async def get_me(self):
                return types.SimpleNamespace(username='DoveraBot')

            async def delete_webhook(self, **kwargs):
                self.delete_webhook_kwargs = kwargs

        class RuntimeDispatcher:
            def include_routers(self, *_routers):
                pass

            async def start_polling(self, *_args, **_kwargs):
                raise RuntimeError('polling stopped')

        session = Session()
        bot = RuntimeBot()
        with mock.patch.object(main, 'Bot', return_value=bot), mock.patch.object(
            main, 'Dispatcher', return_value=RuntimeDispatcher(),
        ), mock.patch.object(
            main.aiohttp, 'ClientSession', return_value=session, create=True,
        ):
            with self.assertRaisesRegex(RuntimeError, 'polling stopped'):
                await main.main_()

        self.assertEqual(bot.delete_webhook_kwargs, {'drop_pending_updates': False})
        self.assertTrue(session.closed)
        self.assertIsNone(main.me.api_session)


class CommonApiSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_reuses_runtime_session_and_logs_request_failure(self):
        install_dependency_stubs(stub_common=False)
        common = import_fresh('common')

        class Response:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                pass

            async def json(self):
                return {'ok': True}

        class Session:
            closed = False
            fail = False

            def __init__(self):
                self.requests = []

            def request(self, *args, **kwargs):
                self.requests.append((args, kwargs))
                if self.fail:
                    raise OSError('offline')
                return Response()

        session = Session()
        common.me.api_session = session

        self.assertEqual(await common.Misc.api_request('/one'), (200, {'ok': True}))
        self.assertEqual(await common.Misc.api_request('/two'), (200, {'ok': True}))
        self.assertFalse(session.closed)
        self.assertEqual(len(session.requests), 2)

        session.fail = True
        with self.assertLogs(level='ERROR') as logs:
            self.assertEqual(await common.Misc.api_request('/offline'), (None, None))
        self.assertIn('API request failed: GET /offline', logs.output[0])


if __name__ == '__main__':
    unittest.main()
