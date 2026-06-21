import unittest
from unittest import mock

from bot_test_harness import (
    FakeCallback,
    FakeMessage,
    FakeState,
    import_fresh,
    install_dependency_stubs,
)


class LegacyRelativesCallbackFeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_relatives = import_fresh('handler_relatives')

    async def test_malformed_parent_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.FATHER}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_relatives.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(),
        ) as check_owner:
            await self.handler_relatives.cbq_papa_mama(callback, FakeState())

        check_owner.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_parent_callback_auth_failure_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.FATHER}{self.common.KeyboardType.SEP}person-uuid'
        )

        with mock.patch.object(
            self.handler_relatives.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ):
            await self.handler_relatives.cbq_papa_mama(callback, FakeState())

        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

    async def test_new_parent_command_interrupt_stops_profile_creation(self):
        message = FakeMessage(text='/map')
        state = FakeState({'uuid': 'person-uuid', 'is_father': True})

        with mock.patch.object(
            self.handler_relatives,
            'is_it_command',
            mock.AsyncMock(return_value=True),
        ), mock.patch.object(
            self.handler_relatives.Misc,
            'api_request',
            mock.AsyncMock(),
        ) as api_request:
            await self.handler_relatives.put_new_papa_mama(message, state)

        api_request.assert_not_awaited()
        self.assertEqual(message.replies, [])

if __name__ == '__main__':
    unittest.main()
