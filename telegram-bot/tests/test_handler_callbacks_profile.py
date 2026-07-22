import types
import unittest
from unittest import mock

from bot_test_harness import (
    FakeBot,
    FakeCallback,
    FakeMessage,
    FakeState,
    import_fresh,
    install_dependency_stubs,
)


class LegacyProfileMediaCallbackFeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_callbacks = import_fresh('handler_callbacks')

    async def test_malformed_photo_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.PHOTO}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(),
        ) as check_owner:
            await self.handler_callbacks.cbq_photo(callback, FakeState())

        check_owner.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_photo_callback_auth_failure_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.PHOTO}{self.common.KeyboardType.SEP}person-uuid'
            f'{self.common.KeyboardType.SEP}22{self.common.KeyboardType.SEP}0'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ):
            await self.handler_callbacks.cbq_photo(callback, FakeState())

        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

class LegacyProfileEditCallbackParserTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_callbacks = import_fresh('handler_callbacks')

    async def test_malformed_new_person_gender_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback('bad~')
        state = FakeState({'uuid': 'person-uuid', 'first_name': 'Person'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_callbacks.cbq_gender_new_person(callback, state)

        post_tg_user.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_malformed_gender_state_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback('bad~')
        state = FakeState({'uuid': 'person-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_callbacks.cbq_gender_from_state(callback, state)

        post_tg_user.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_gender_state_auth_failure_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.GENDER_MALE}{self.common.KeyboardType.SEP}'
        )
        state = FakeState({'uuid': 'person-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, {'uuid': 'requester-uuid'})),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'put_user_properties',
            mock.AsyncMock(),
        ) as put_user_properties:
            await self.handler_callbacks.cbq_gender_from_state(callback, state)

        put_user_properties.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

    async def test_meet_gender_auth_failure_shows_profile_notice_before_state_use(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.MEET_GENDER_MALE}{self.common.KeyboardType.SEP}'
        )
        state = FakeState({'uuid': 'person-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'put_user_properties',
            mock.AsyncMock(),
        ) as put_user_properties:
            await self.handler_callbacks.cbq_meet_ask_gender(callback, state)

        put_user_properties.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

    async def test_malformed_attitude_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.TRUST_THANK}{self.common.KeyboardType.SEP}bad'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_callbacks.cbq_attitude(callback, FakeState())

        post_tg_user.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_malformed_dates_dod_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.DATES_DOD_NONE}{self.common.KeyboardType.SEP}'
        )
        state = FakeState({'uuid': 'person-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(),
        ) as check_owner:
            await self.handler_callbacks.cbq_dates_dod_done_or_dead(callback, state)

        check_owner.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_malformed_meet_action_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.MEET_DO}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_callbacks.cbq_meet_do_or_revoke(callback, FakeState())

        post_tg_user.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_meet_action_callback_preserves_inviter_sid(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.MEET_DO}'
            f'{self.common.KeyboardType.SEP}abcdefghij'
            f'{self.common.KeyboardType.SEP}invite0001'
            f'{self.common.KeyboardType.SEP}'
        )
        profile = {
            'uuid': 'profile-uuid',
            'username': 'abcdefghij',
            'first_name': 'Person',
            'is_active': True,
            'did_meet': False,
            'gender': 'm',
            'dob': '2000-01-01',
            'latitude': None,
            'longitude': None,
            'has_bank': False,
            'has_tgdesc': True,
        }

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, profile)),
        ), mock.patch.object(
            self.handler_callbacks,
            'meet_do_or_revoke',
            mock.AsyncMock(),
        ) as meet_do_or_revoke:
            await self.handler_callbacks.cbq_meet_do_or_revoke(callback, FakeState())

        meet_do_or_revoke.assert_awaited_once()
        data = meet_do_or_revoke.await_args.args[0]
        self.assertEqual(data['what'], self.common.KeyboardType.MEET_DO)
        self.assertEqual(data['username_from'], 'abcdefghij')
        self.assertEqual(data['username_inviter'], 'invite0001')
        self.assertTrue(callback.answered)

class LegacyProfileEditCallbackFeedbackFinishTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_callbacks = import_fresh('handler_callbacks')

    def assert_stale_notice(self, callback):
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    def assert_profile_notice(self, callback):
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

    async def test_malformed_iof_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.IOF}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(),
        ) as check_owner:
            await self.handler_callbacks.cbq_existing_iof(callback, FakeState())

        check_owner.assert_not_awaited()
        self.assert_stale_notice(callback)

    async def test_comment_auth_failure_shows_profile_notice_and_skips_prompt(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.COMMENT}{self.common.KeyboardType.SEP}person-uuid'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ):
            await self.handler_callbacks.cbq_comment(callback, FakeState())

        self.assert_profile_notice(callback)
        self.assertEqual(callback.message.replies, [])

    async def test_dob_unknown_auth_failure_clears_state_and_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.DATES_DOB_UNKNOWN}{self.common.KeyboardType.SEP}person-uuid'
        )
        state = FakeState({'uuid': 'person-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ):
            await self.handler_callbacks.cbq_dates_dob_unknown(callback, state)

        self.assertTrue(state.cleared)
        self.assert_profile_notice(callback)

    async def test_delete_confirmed_state_mismatch_shows_notice_and_skips_delete_api(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.DELETE_USER_CONFIRMED}{self.common.KeyboardType.SEP}person-uuid'
        )
        state = FakeState({'uuid': 'other-uuid', 'owner_id': 42})
        response_check = {
            'uuid': 'owner-uuid',
            'user_id': 42,
            'response_uuid': {'uuid': 'person-uuid'},
        }

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=response_check),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'api_request',
            mock.AsyncMock(),
        ) as api_request:
            await self.handler_callbacks.cbq_delete_user_confirmed(callback, state)

        api_request.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_stale_notice(callback)

    async def test_delete_confirmed_api_validation_uses_delete_response_message(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.DELETE_USER_CONFIRMED}{self.common.KeyboardType.SEP}person-uuid'
        )
        state = FakeState({'uuid': 'person-uuid', 'owner_id': 42})
        response_check = {
            'uuid': 'owner-uuid',
            'user_id': 42,
            'response_uuid': {
                'uuid': 'person-uuid',
                'first_name': 'Person',
                'owner': {'uuid': 'owner-uuid'},
                'r_sympa_username': '',
            },
        }

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=response_check),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'api_request',
            mock.AsyncMock(return_value=(400, {'message': 'cannot delete'})),
        ):
            await self.handler_callbacks.cbq_delete_user_confirmed(callback, state)

        self.assertTrue(state.cleared)
        self.assertTrue(callback.answered)
        self.assertFalse(callback.answer_show_alert)
        self.assertIn('cannot delete', callback.message.replies[0].text)

    async def test_undelete_confirmed_auth_failure_clears_state_and_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.UNDELETE_USER_CONFIRMED}{self.common.KeyboardType.SEP}person-uuid'
        )
        state = FakeState({'uuid': 'person-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ):
            await self.handler_callbacks.cbq_udelete_user_confirmed(callback, state)

        self.assertTrue(state.cleared)
        self.assert_profile_notice(callback)

    async def test_send_message_auth_failure_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.SEND_MESSAGE}{self.common.KeyboardType.SEP}person-uuid'
        )
        state = FakeState()

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'get_user_by_uuid',
            mock.AsyncMock(return_value=(200, {'uuid': 'person-uuid', 'first_name': 'Person'})),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_callbacks.cbq_send_message(callback, state)

        self.assertIsNone(state.state)
        self.assert_profile_notice(callback)

    async def test_show_messages_malformed_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.SHOW_MESSAGES}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_callbacks.cbq_show_messages(callback, FakeState())

        post_tg_user.assert_not_awaited()
        self.assert_stale_notice(callback)

    async def test_user_desc_auth_failure_shows_profile_notice_and_skips_profile_lookup(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.USER_DESC}{self.common.KeyboardType.SEP}person-uuid'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, {'uuid': 'other-uuid'})),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'get_user_by_uuid',
            mock.AsyncMock(),
        ) as get_user_by_uuid:
            await self.handler_callbacks.cbq_get_user_desc(callback, FakeState())

        get_user_by_uuid.assert_not_awaited()
        self.assert_profile_notice(callback)

    async def test_banking_auth_failure_shows_profile_notice_and_skips_bank_lookup(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.BANKING}{self.common.KeyboardType.SEP}person-uuid'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, {'uuid': 'other-uuid'})),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'get_bank_details',
            mock.AsyncMock(),
        ) as get_bank_details:
            await self.handler_callbacks.cbq_get_banking(callback, FakeState())

        get_bank_details.assert_not_awaited()
        self.assert_profile_notice(callback)

    async def test_meet_edit_back_auth_failure_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.MEET_EDIT_BACK}{self.common.KeyboardType.SEP}'
            f'person-uuid{self.common.KeyboardType.SEP}3003{self.common.KeyboardType.SEP}'
            f'{self.common.Misc.CARD_TYPE_MEET}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'show_edit_meet',
            mock.AsyncMock(),
        ) as show_edit_meet:
            await self.handler_callbacks.cbq_meet_edit_back(callback, FakeState())

        show_edit_meet.assert_not_awaited()
        self.assert_profile_notice(callback)

    async def test_message_delete_malformed_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.MESSAGE_DELETE}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_callbacks.cbq_message_delete(callback, FakeState())

        post_tg_user.assert_not_awaited()
        self.assert_stale_notice(callback)

class LegacyProfileEditStateFeedbackFinishTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_callbacks = import_fresh('handler_callbacks')

    def assert_stale_state_reply(self, message):
        self.assertEqual(len(message.replies), 1)
        self.assertIn('ввод больше не актуален', message.replies[0].text.lower())

    def assert_profile_reply(self, message):
        self.assertEqual(len(message.replies), 1)
        self.assertIn('профиль', message.replies[0].text.lower())

    async def test_dob_missing_state_replies_and_skips_auth(self):
        message = FakeMessage(text='01.01.1990')
        state = FakeState()

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(),
        ) as check_owner:
            await self.handler_callbacks.process_dob(message, state)

        check_owner.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_stale_state_reply(message)

    async def test_comment_auth_failure_replies_and_skips_update(self):
        message = FakeMessage(text='comment')
        state = FakeState({'uuid': 'person-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'put_user_properties',
            mock.AsyncMock(),
        ) as put_user_properties:
            await self.handler_callbacks.process_comment(message, state)

        put_user_properties.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_profile_reply(message)

    async def test_send_message_api_exception_replies_and_clears(self):
        message = FakeMessage(text='hello')
        state = FakeState({
            'uuid_pack': 'pack-uuid',
            'profile_from': {'uuid': 'from-uuid', 'first_name': 'From'},
            'profile_to': {
                'uuid': 'to-uuid',
                'username': 'to-user',
                'first_name': 'To',
                'owner': None,
                'tg_data': [{'tg_uid': 3003}],
            },
        })

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'redis_is_key_first_up',
            mock.Mock(return_value=True),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'api_request',
            mock.AsyncMock(side_effect=RuntimeError('api down')),
        ):
            await self.handler_callbacks.process_message_to_send(message, state)

        self.assertTrue(state.cleared)
        self.assertEqual(len(message.replies), 1)
        self.assertIn(self.common.Misc.MSG_ERROR_API.lower(), message.replies[0].text.lower())

    async def test_send_message_rejects_non_person_stale_state_before_delivery(self):
        message = FakeMessage(text='hello')
        state = FakeState({
            'uuid_pack': 'pack-uuid',
            'profile_from': {'uuid': 'from-uuid', 'first_name': 'From'},
            'profile_to': {
                'uuid': 'to-uuid', 'username': 'helper_bot', 'first_name': 'Bot',
                'owner': None, 'tg_data': [{'tg_uid': 3003}],
                'is_org': True, 'is_person': False,
            },
        })

        with mock.patch.object(
            self.handler_callbacks.Misc, 'api_request', mock.AsyncMock(),
        ) as api_request, mock.patch.object(
            self.handler_callbacks, 'bot', FakeBot(),
        ) as bot:
            await self.handler_callbacks.process_message_to_send(message, state)

        api_request.assert_not_awaited()
        self.assertFalse(bot.sent_messages)
        self.assertTrue(state.cleared)
        self.assertIn('нельзя написать', message.replies[0].text.lower())

    async def test_send_message_api_rejection_aborts_delivery(self):
        message = FakeMessage(text='hello')
        state = FakeState({
            'uuid_pack': 'pack-uuid',
            'profile_from': {'uuid': 'from-uuid', 'first_name': 'From'},
            'profile_to': {
                'uuid': 'to-uuid', 'username': 'to-user', 'first_name': 'To',
                'owner': None, 'tg_data': [{'tg_uid': 3003}],
                'is_person': True,
            },
        })

        with mock.patch.object(
            self.handler_callbacks.Misc, 'redis_is_key_first_up', mock.Mock(return_value=True),
        ), mock.patch.object(
            self.handler_callbacks.Misc, 'api_request',
            mock.AsyncMock(return_value=(400, {'message': 'rejected'})),
        ), mock.patch.object(
            self.handler_callbacks, 'bot', FakeBot(),
        ) as bot:
            await self.handler_callbacks.process_message_to_send(message, state)

        self.assertFalse(bot.sent_messages)
        self.assertTrue(state.cleared)
        self.assertEqual(message.replies[0].text, 'rejected')

    async def test_user_desc_auth_failure_replies_and_skips_update(self):
        message = FakeMessage(text='description')
        state = FakeState({'uuid': 'person-uuid', 'uuid_pack': 'pack-uuid'})

        with mock.patch.object(
            self.handler_callbacks.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'put_user_properties',
            mock.AsyncMock(),
        ) as put_user_properties:
            await self.handler_callbacks.process_get_user_desc(message, state)

        put_user_properties.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_profile_reply(message)

    async def test_existing_iof_command_interrupt_skips_profile_update(self):
        message = FakeMessage(text='/start')
        state = FakeState({'uuid': 'person-uuid'})

        async def command_interrupt(message, state):
            await state.clear()
            await message.reply(f'{self.common.Misc.MSG_YOU_CANCELLED_INPUT}\nВыполняю команду /start')
            return True

        with mock.patch.object(
            self.handler_callbacks,
            'is_it_command',
            mock.AsyncMock(side_effect=command_interrupt),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'put_user_properties',
            mock.AsyncMock(),
        ) as put_user_properties:
            await self.handler_callbacks.process_existing_iof(message, state)

        put_user_properties.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assertEqual(len(message.replies), 1)
        self.assertIn('выполняю команду', message.replies[0].text.lower())

class LegacyMeetDeeplinkTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.handler_callbacks = import_fresh('handler_callbacks')

    async def test_send_qr_uses_runtime_bot_username(self):
        fake_bot = FakeBot()
        self.handler_callbacks.bot = fake_bot
        profile = {'uuid': 'profile-uuid'}
        tg_user = types.SimpleNamespace(id=5454)
        qr_buffer = types.SimpleNamespace(getvalue=lambda: b'qr', name='qr.png')
        expected_url = 'https://t.me/DoveraBot?start=m-meet-token'

        with mock.patch.object(
            self.handler_callbacks.MeetId,
            'meetId_by_profile',
            mock.AsyncMock(return_value='meet-token'),
        ), mock.patch.object(
            self.handler_callbacks.Misc,
            'get_qrcode',
            mock.AsyncMock(return_value=qr_buffer),
        ) as get_qrcode:
            await self.handler_callbacks.send_qr(profile, tg_user)

        get_qrcode.assert_awaited_once_with(profile, expected_url)
        self.assertEqual(len(fake_bot.sent_photos), 1)
        self.assertEqual(fake_bot.sent_photos[0][0], 5454)
        self.assertIn(expected_url, fake_bot.sent_photos[0][2])

if __name__ == '__main__':
    unittest.main()
