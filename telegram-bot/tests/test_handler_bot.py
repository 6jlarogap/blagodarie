import unittest
from unittest import mock

try:
    from .bot_test_harness import (
        FakeCallback,
        FakeMessage,
        FakeState,
        import_fresh,
        install_dependency_stubs,
    )
except ImportError:
    from bot_test_harness import (
        FakeCallback,
        FakeMessage,
        FakeState,
        import_fresh,
        install_dependency_stubs,
    )


class PrivateEntryFeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.handler_bot = import_fresh('handler_bot')

    async def test_message_to_bot_auth_failure_replies_with_api_error(self):
        message = FakeMessage(text='hello')

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_bot.message_to_bot(message, FakeState())

        self.assertEqual([reply.text for reply in message.replies], [self.handler_bot.Misc.MSG_ERROR_API])

    async def test_cmd_start_deeplink_auth_failure_replies_with_api_error(self):
        message = FakeMessage(text='/start abcdefghij')

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_bot.cmd_start(message, FakeState())

        self.assertEqual([reply.text for reply in message.replies], [self.handler_bot.Misc.MSG_ERROR_API])

    async def test_forwarded_friend_target_auth_failure_replies_with_api_error(self):
        message = FakeMessage(text='forwarded hello')
        origin = self.handler_bot.MessageOriginUser()
        origin.sender_user = mock.Mock(
            id=2002,
            username='friend',
            first_name='Friend',
            last_name='User',
            is_bot=False,
        )
        message.forward_origin = origin

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(side_effect=[
                (200, {'uuid': 'requester-uuid', 'first_name': 'Requester'}),
                (500, {}),
            ]),
        ) as post_tg_user, mock.patch.object(
            self.handler_bot.Misc,
            'show_card',
            mock.AsyncMock(),
        ) as show_card:
            await self.handler_bot.message_to_bot(message, FakeState())

        self.assertEqual(post_tg_user.await_count, 2)
        show_card.assert_not_awaited()
        self.assertEqual([reply.text for reply in message.replies], [self.handler_bot.Misc.MSG_ERROR_API])

    async def test_agree_to_rules_auth_failure_shows_alert_and_keeps_state(self):
        callback = FakeCallback('70~agree')
        state = FakeState()

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_bot.Misc,
            'show_card',
            mock.AsyncMock(),
        ) as show_card:
            await self.handler_bot.cbq_agree_to_rules(callback, state)

        show_card.assert_not_awaited()
        self.assertFalse(state.cleared)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertEqual(callback.answer_text, self.handler_bot.Misc.MSG_ERROR_API)

    async def test_agree_to_rules_success_shows_card_and_clears_state(self):
        callback = FakeCallback('70~agree')
        state = FakeState()
        profile = {'uuid': 'user-uuid', 'first_name': 'Friend'}

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, profile)),
        ), mock.patch.object(
            self.handler_bot.Misc,
            'show_card',
            mock.AsyncMock(),
        ) as show_card:
            await self.handler_bot.cbq_agree_to_rules(callback, state)

        show_card.assert_awaited_once_with(
            profile=profile,
            profile_sender=profile,
            tg_user_sender=callback.from_user,
        )
        self.assertTrue(state.cleared)
        self.assertTrue(callback.answered)
        self.assertFalse(callback.answer_show_alert)
        self.assertIsNone(callback.answer_text)


if __name__ == '__main__':
    unittest.main()
