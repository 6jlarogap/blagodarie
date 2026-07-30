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

    def test_telegram_username_input_accepts_only_exact_public_profiles(self):
        allowed = {
            '@Pending_Name': 'pending_name',
            'https://t.me/Pending_Name': 'pending_name',
            'https://t.me/Pending_Name/': 'pending_name',
        }
        rejected = (
            '', 'pending_name', ' @pending_name', '@pending_name ',
            'hello @pending_name', '@pending_name @other_name',
            'http://t.me/pending_name', 'https://telegram.me/pending_name',
            'https://www.t.me/pending_name', 'https://evil.test/@t.me/pending_name',
            'https://user@t.me/pending_name', 'https://t.me:443/pending_name',
            'https://t.me/pending_name?start=1', 'https://t.me/pending_name?',
            'https://t.me/pending_name#post', 'https://t.me/pending_name#',
            'https://t.me/pending_name;param', 'https://t.me/pending_name/123',
            'https://t.me/c/123/456', 'https://t.me/s/pending_name',
            'https://t.me/joinchat', 'https://t.me/joinchat/',
            'https://t.me/joinchat/abcde', 'https://t.me/share',
            'https://t.me/share/', 'https://t.me/share/url',
            'https://t.me/+invite', 'https://t.me/pending_name//',
            'https://t.me/pending_name https://t.me/other_name',
            'look https://t.me/pending_name', 'https://[',
            '\x00https://t.me/pending_name', '\x1fhttps://t.me/pending_name',
        )

        for text, username in allowed.items():
            with self.subTest(text=text):
                self.assertEqual(self.handler_bot._telegram_username_input(text), username)
        for text in rejected:
            with self.subTest(text=text):
                self.assertEqual(self.handler_bot._telegram_username_input(text), '')

    async def test_exact_username_inputs_reuse_one_pending_profile_and_show_card(self):
        sender = {'user_id': 1, 'uuid': 'sender-uuid'}
        target = {'user_id': 2, 'uuid': 'target-uuid', 'pending_tg_username': 'pending_name'}

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, sender)),
        ), mock.patch.object(
            self.handler_bot.Misc,
            'get_or_create_tg_username',
            mock.AsyncMock(return_value=(200, target)),
        ) as get_or_create, mock.patch.object(
            self.handler_bot.Misc,
            'show_card',
            mock.AsyncMock(),
        ) as show_card:
            for text in ('@Pending_Name', 'https://t.me/Pending_Name', 'https://t.me/Pending_Name/'):
                await self.handler_bot.message_to_bot(FakeMessage(text=text), FakeState())

        self.assertEqual(
            get_or_create.await_args_list,
            [mock.call('pending_name'), mock.call('pending_name'), mock.call('pending_name')],
        )
        self.assertEqual(show_card.await_count, 3)

    async def test_non_exact_forwarded_or_group_input_never_creates_pending_profile(self):
        sender = {'user_id': 1, 'uuid': 'sender-uuid'}
        cases = (
            ('hello @pending_name', False, self.handler_bot.ChatType.PRIVATE),
            ('@pending_name @other_name', False, self.handler_bot.ChatType.PRIVATE),
            ('look https://t.me/pending_name', False, self.handler_bot.ChatType.PRIVATE),
            ('https://t.me/pending_name https://t.me/other_name', False, self.handler_bot.ChatType.PRIVATE),
            (' @pending_name ', False, self.handler_bot.ChatType.PRIVATE),
            (' https://t.me/pending_name ', False, self.handler_bot.ChatType.PRIVATE),
            ('\x00https://t.me/pending_name', False, self.handler_bot.ChatType.PRIVATE),
            ('@pending_name', True, self.handler_bot.ChatType.PRIVATE),
            ('https://t.me/pending_name', False, self.handler_bot.ChatType.GROUP),
        )
        for text, forwarded, chat_type in cases:
            message = FakeMessage(text=text)
            message.chat.type = chat_type
            if forwarded:
                origin = self.handler_bot.MessageOriginUser()
                origin.sender_user = message.from_user
                message.forward_origin = origin
            with mock.patch.object(
                self.handler_bot.Misc,
                'post_tg_user',
                mock.AsyncMock(return_value=(200, sender)),
            ), mock.patch.object(
                self.handler_bot.Misc,
                'get_or_create_tg_username',
                mock.AsyncMock(),
            ) as get_or_create, mock.patch.object(
                self.handler_bot.Misc,
                'api_request',
                mock.AsyncMock(return_value=(200, [])),
            ), mock.patch.object(
                self.handler_bot.Misc,
                'text_search_phrase',
                return_value='',
            ):
                await self.handler_bot.message_to_bot(message, FakeState())
            get_or_create.assert_not_awaited()

    async def test_cmd_start_deeplink_auth_failure_replies_with_api_error(self):
        message = FakeMessage(text='/start abcdefghij')

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_bot.cmd_start(message, FakeState())

        self.assertEqual([reply.text for reply in message.replies], [self.handler_bot.Misc.MSG_ERROR_API])

    async def test_update_profile_updates_telegram_data_photo_and_shows_card(self):
        message = FakeMessage(text='/update_profile')
        message.from_user.first_name = 'New'
        message.from_user.last_name = 'Name'
        old_profile = {'uuid': 'user-uuid'}
        updated_profile = {'uuid': 'user-uuid', 'first_name': 'Name New'}

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, old_profile)),
        ) as post_tg_user, mock.patch.object(
            self.handler_bot.Misc,
            'get_user_photo',
            mock.AsyncMock(return_value='base64-photo'),
        ), mock.patch.object(
            self.handler_bot.Misc,
            'put_user_properties',
            mock.AsyncMock(return_value=(200, updated_profile)),
        ) as put_user_properties, mock.patch.object(
            self.handler_bot.Misc,
            'show_card',
            mock.AsyncMock(),
        ) as show_card:
            await self.handler_bot.cmd_update_profile(message, FakeState())

        post_tg_user.assert_awaited_once_with(message.from_user)
        put_user_properties.assert_awaited_once_with(
            uuid='user-uuid',
            first_name='New',
            last_name='Name',
            photo='base64-photo',
        )
        show_card.assert_awaited_once_with(
            profile=updated_profile,
            profile_sender=updated_profile,
            tg_user_sender=message.from_user,
        )

    async def test_update_profile_without_telegram_photo_preserves_existing_photo(self):
        message = FakeMessage(text='/update_profile')

        with mock.patch.object(
            self.handler_bot.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, {'uuid': 'user-uuid'})),
        ), mock.patch.object(
            self.handler_bot.Misc,
            'get_user_photo',
            mock.AsyncMock(return_value=None),
        ), mock.patch.object(
            self.handler_bot.Misc,
            'put_user_properties',
            mock.AsyncMock(return_value=(500, {})),
        ) as put_user_properties, mock.patch.object(
            self.handler_bot.Misc,
            'show_card',
            mock.AsyncMock(),
        ) as show_card:
            await self.handler_bot.cmd_update_profile(message, FakeState())

        put_user_properties.assert_awaited_once_with(
            uuid='user-uuid',
            first_name='Requester',
            last_name='',
        )
        show_card.assert_not_awaited()
        self.assertEqual(
            [reply.text for reply in message.replies],
            [self.handler_bot.Misc.MSG_ERROR_API],
        )

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
        self.assertEqual(post_tg_user.await_args_list[1].kwargs, {'did_bot_start': False})
        show_card.assert_not_awaited()
        self.assertEqual([reply.text for reply in message.replies], [self.handler_bot.Misc.MSG_ERROR_API])

    async def test_visible_bot_and_channel_forwards_use_authoritative_subject_paths(self):
        sender = {'uuid': 'requester-uuid', 'first_name': 'Requester'}
        targets = (
            (self.handler_bot.MessageOriginUser, 'sender_user', mock.Mock(
                id=2002, username='helper_bot', first_name='Helper', last_name='', is_bot=True,
            ), 'post_tg_user'),
            (self.handler_bot.MessageOriginChannel, 'chat', mock.Mock(
                id=-1002003, username='news', title='News', type='channel',
            ), 'post_tg_chat'),
        )
        for origin_type, attribute, forwarded, expected_method in targets:
            message = FakeMessage(text='forwarded')
            origin = origin_type()
            setattr(origin, attribute, forwarded)
            message.forward_origin = origin
            target = {'uuid': 'target-uuid', 'first_name': 'Target'}
            with mock.patch.object(
                self.handler_bot.Misc, 'post_tg_user',
                mock.AsyncMock(return_value=(200, sender)),
            ) as post_user, mock.patch.object(
                self.handler_bot.Misc, 'post_tg_chat',
                mock.AsyncMock(return_value=(200, target)),
            ) as post_chat, mock.patch.object(
                self.handler_bot.Misc, 'show_card', mock.AsyncMock(),
            ) as show_card:
                if expected_method == 'post_tg_user':
                    post_user.side_effect = [(200, sender), (200, target)]
                await self.handler_bot.message_to_bot(message, FakeState())

            if expected_method == 'post_tg_chat':
                post_chat.assert_awaited_once_with(forwarded)
            else:
                self.assertEqual(post_user.await_count, 2)
                self.assertEqual(post_user.await_args_list[1].kwargs, {'did_bot_start': False})
            show_card.assert_awaited_once()

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
