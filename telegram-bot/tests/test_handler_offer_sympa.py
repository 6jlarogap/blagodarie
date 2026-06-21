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


class OfferCallbackFeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_offer = import_fresh('handler_offer')

    async def test_malformed_offer_answer_shows_notice_and_skips_auth(self):
        callback = FakeCallback('44~offer-uuid')

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_offer.cbq_offer_answer(callback, FakeState())

        post_tg_user.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_offer_answer_auth_failure_shows_profile_notice(self):
        callback = FakeCallback('44~offer-uuid~1~')

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_offer.cbq_offer_answer(callback, FakeState())

        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

class OfferSympaFeedbackCoverageTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_offer = import_fresh('handler_offer')
        self.handler_sympas = import_fresh('handler_sympas')

    def assert_stale_notice(self, callback):
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    def assert_profile_notice(self, callback):
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

    def assert_api_notice(self, callback):
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn(self.common.Misc.MSG_ERROR_API.lower(), callback.answer_text.lower())

    def assert_stale_reply(self, message):
        self.assertEqual(len(message.replies), 1)
        self.assertIn('ввод больше не актуален', message.replies[0].text.lower())

    def assert_profile_reply(self, message):
        self.assertEqual(len(message.replies), 1)
        self.assertIn('профиль', message.replies[0].text.lower())

    def assert_api_reply(self, message):
        self.assertEqual(len(message.replies), 1)
        self.assertIn(self.common.Misc.MSG_ERROR_API.lower(), message.replies[0].text.lower())

    def offer_profile(self):
        return {'uuid': 'requester-uuid', 'username': 'requester', 'first_name': 'Requester'}

    def offer_donate_state(self):
        return {
            'profile_to': {
                'uuid': 'target-uuid',
                'username': 'targetuser',
                'first_name': 'Target',
                'tg_data': [],
            },
            'profile_from': self.offer_profile(),
            'journal_id': 77,
            'uuid_pack': 'offer-pack',
            'offer_uuid': 'offer-uuid',
            'username_ref': 'referrer',
        }

    def sympa_profiles(self):
        profile_from = {
            'uuid': 'man-uuid',
            'username': 'manuser123',
            'first_name': 'Man',
            'r_sympa_username': 'woman12345',
            'is_active': True,
            'did_meet': True,
            'gender': 'm',
            'tg_data': [{'tg_uid': 3003}],
        }
        profile_to = {
            'uuid': 'woman-uuid',
            'username': 'woman12345',
            'first_name': 'Woman',
            'r_sympa_username': 'manuser123',
            'is_active': True,
            'did_meet': True,
            'gender': 'f',
            'photo': '',
            'tg_data': [{'tg_uid': 3004}],
        }
        return profile_from, profile_to

    def sympa_donate_state(self):
        user_m, user_f = self.sympa_profiles()
        return {
            'journal_id': 88,
            'uuid_pack': 'sympa-pack',
            'response_get_donate': {
                'user_m': {'uuid': user_m['uuid']},
                'user_f': user_f,
                'donate': {
                    'tg_data': [],
                    'profile': {'username': 'donor12345'},
                },
            },
        }

    async def test_offer_geo_pass_missing_state_shows_stale_notice_and_skips_create(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.OFFER_GEO_PASS}{self.common.KeyboardType.SEP}'
        )
        state = FakeState()

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, self.offer_profile())),
        ), mock.patch.object(
            self.handler_offer.Offer,
            'create_offer',
            mock.AsyncMock(),
        ) as create_offer:
            await self.handler_offer.cbq_offer_geo_pass(callback, state)

        create_offer.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_stale_notice(callback)

    async def test_offer_location_auth_failure_replies_and_skips_create(self):
        message = FakeMessage(text='55.75,37.61')
        state = FakeState({'create_offer_dict': {'user_uuid': 'requester-uuid'}})

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_offer.Offer,
            'create_offer',
            mock.AsyncMock(),
        ) as create_offer:
            await self.handler_offer.process_offer_location(message, state)

        create_offer.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_profile_reply(message)

    async def test_malformed_donate_offer_choice_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.DONATE_OFFER_CHOICE}'
            f'{self.common.KeyboardType.SEP}bad'
            f'{self.common.KeyboardType.SEP}targetuser'
            f'{self.common.KeyboardType.SEP}referrer'
            f'{self.common.KeyboardType.SEP}offer-id'
        )

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_offer.cbq_donate_offer_choice(callback, FakeState())

        post_tg_user.assert_not_awaited()
        self.assert_stale_notice(callback)

    async def test_donate_offer_choice_auth_failure_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.DONATE_OFFER_CHOICE}'
            f'{self.common.KeyboardType.SEP}77'
            f'{self.common.KeyboardType.SEP}targetuser'
            f'{self.common.KeyboardType.SEP}referrer'
            f'{self.common.KeyboardType.SEP}offer-id'
        )

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_offer.cbq_donate_offer_choice(callback, FakeState())

        self.assert_profile_notice(callback)

    async def test_offer_donate_message_missing_state_replies_and_skips_auth(self):
        message = FakeMessage(text='receipt')
        state = FakeState()

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_offer.process_message_thank_office_choice(message, state)

        post_tg_user.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_stale_reply(message)

    async def test_offer_donate_message_auth_failure_replies_and_skips_thank_api(self):
        message = FakeMessage(text='receipt')
        state = FakeState(self.offer_donate_state())

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_offer.Misc,
            'api_request',
            mock.AsyncMock(),
        ) as api_request:
            await self.handler_offer.process_message_thank_office_choice(message, state)

        api_request.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_profile_reply(message)

    async def test_offer_donate_message_api_failure_replies_and_clears(self):
        message = FakeMessage(text='receipt')
        state = FakeState(self.offer_donate_state())

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, self.offer_profile())),
        ), mock.patch.object(
            self.handler_offer.Misc,
            'redis_is_key_first_up',
            mock.Mock(return_value=True),
        ), mock.patch.object(
            self.handler_offer.Misc,
            'api_request',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_offer.process_message_thank_office_choice(message, state)

        self.assertTrue(state.cleared)
        self.assert_api_reply(message)

    async def test_offer_donate_message_command_interrupt_skips_thank_api(self):
        message = FakeMessage(text='/start')
        state = FakeState(self.offer_donate_state())

        with mock.patch.object(
            self.handler_offer,
            'is_it_command',
            mock.AsyncMock(return_value=True),
        ), mock.patch.object(
            self.handler_offer.Misc,
            'api_request',
            mock.AsyncMock(),
        ) as api_request:
            await self.handler_offer.process_message_thank_office_choice(message, state)

        api_request.assert_not_awaited()
        self.assertFalse(state.cleared)
        self.assertEqual(message.replies, [])

    async def test_offer_message_delivery_success_still_sends_and_clears(self):
        message = FakeMessage(text='hello voters')
        state = FakeState({'uuid': 'requester-uuid', 'offer_uuid': 'offer-uuid'})
        fake_bot = FakeBot()
        self.handler_offer.bot = fake_bot

        with mock.patch.object(
            self.handler_offer.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, self.offer_profile())),
        ), mock.patch.object(
            self.handler_offer.Misc,
            'api_request',
            mock.AsyncMock(return_value=(200, {
                'question': 'Question',
                'users': [{'tg_data': [{'tg_uid': 5005}]}],
            })),
        ):
            await self.handler_offer.process_message_to_offer(message, state)

        self.assertTrue(state.cleared)
        self.assertEqual(len(fake_bot.sent_messages), 1)
        self.assertEqual(len(fake_bot.copied_messages), 1)
        self.assertIn('Сообщение отправлено 1 адресату', message.replies[0].text)

    async def test_sympa_donate_message_command_interrupt_skips_auth(self):
        message = FakeMessage(text='/start')
        state = FakeState(self.sympa_donate_state())

        with mock.patch.object(
            self.handler_sympas,
            'is_it_command',
            mock.AsyncMock(return_value=True),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_sympas.process_message_donate_after_sympa(message, state)

        post_tg_user.assert_not_awaited()
        self.assertFalse(state.cleared)
        self.assertEqual(message.replies, [])

    async def test_sympa_donate_message_missing_state_replies_and_skips_auth(self):
        message = FakeMessage(text='receipt')
        state = FakeState()

        with mock.patch.object(
            self.handler_sympas.Misc,
            'post_tg_user',
            mock.AsyncMock(),
        ) as post_tg_user:
            await self.handler_sympas.process_message_donate_after_sympa(message, state)

        post_tg_user.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_stale_reply(message)

    async def test_sympa_donate_message_auth_failure_replies_and_skips_thank_api(self):
        message = FakeMessage(text='receipt')
        state = FakeState(self.sympa_donate_state())

        with mock.patch.object(
            self.handler_sympas.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'api_request',
            mock.AsyncMock(),
        ) as api_request:
            await self.handler_sympas.process_message_donate_after_sympa(message, state)

        api_request.assert_not_awaited()
        self.assertTrue(state.cleared)
        self.assert_profile_reply(message)

    async def test_sympa_donate_message_api_failure_replies_and_clears(self):
        message = FakeMessage(text='receipt')
        state = FakeState(self.sympa_donate_state())
        profile_from = self.sympa_profiles()[0]

        with mock.patch.object(
            self.handler_sympas.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, profile_from)),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'redis_is_key_first_up',
            mock.Mock(return_value=True),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'api_request',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_sympas.process_message_donate_after_sympa(message, state)

        self.assertTrue(state.cleared)
        self.assert_api_reply(message)

    async def test_sympa_donate_callback_api_failure_shows_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.SYMPA_DONATE}'
            f'{self.common.KeyboardType.SEP}manuser123'
            f'{self.common.KeyboardType.SEP}woman12345'
            f'{self.common.KeyboardType.SEP}88'
        )
        profile_from, profile_to = self.sympa_profiles()

        with mock.patch.object(
            self.handler_sympas.Common,
            'check_common_callback',
            mock.AsyncMock(return_value=(profile_from, profile_to, 88)),
        ), mock.patch.object(
            self.handler_sympas.Common,
            'is_any_not_active',
            mock.AsyncMock(return_value=False),
        ), mock.patch.object(
            self.handler_sympas.Common,
            'make2_donate',
            mock.AsyncMock(return_value=(None, None, None)),
        ):
            await self.handler_sympas.cbq_get_sympa_donate(callback, FakeState())

        self.assert_api_notice(callback)

    async def test_sympa_hide_api_failure_shows_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.SYMPA_HIDE}'
            f'{self.common.KeyboardType.SEP}manuser123'
            f'{self.common.KeyboardType.SEP}woman12345'
            f'{self.common.KeyboardType.SEP}88'
        )
        profile_from, profile_to = self.sympa_profiles()

        with mock.patch.object(
            self.handler_sympas.Common,
            'check_common_callback',
            mock.AsyncMock(return_value=(profile_from, profile_to, 88)),
        ), mock.patch.object(
            self.handler_sympas.Common,
            'is_any_not_active',
            mock.AsyncMock(return_value=False),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'api_request',
            mock.AsyncMock(return_value=(500, {})),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'remove_n_send_message',
            mock.AsyncMock(),
        ) as remove_n_send_message:
            await self.handler_sympas.cbq_sympa_hide(callback, FakeState())

        remove_n_send_message.assert_not_awaited()
        self.assert_api_notice(callback)

    async def test_sympa_missing_journal_shows_stale_notice_and_skips_profile_lookup(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.SYMPA_HIDE}'
            f'{self.common.KeyboardType.SEP}manuser123'
            f'{self.common.KeyboardType.SEP}woman12345'
            f'{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_sympas.Misc,
            'check_owner_by_sid',
            mock.AsyncMock(),
        ) as check_owner, mock.patch.object(
            self.handler_sympas.Misc,
            'get_user_by_sid',
            mock.AsyncMock(),
        ) as get_user:
            await self.handler_sympas.cbq_sympa_hide(callback, FakeState())

        check_owner.assert_not_awaited()
        get_user.assert_not_awaited()
        self.assert_stale_notice(callback)

class LegacySympaLinkTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.handler_sympas = import_fresh('handler_sympas')

    async def test_contact_handoff_profile_link_uses_runtime_bot_username(self):
        callback = FakeCallback('73~woman~man~123')
        state = FakeState()
        profile_from = {
            'username': 'woman',
            'first_name': 'Woman',
            'r_sympa_username': 'man',
            'is_active': True,
            'did_meet': True,
            'gender': 'f',
            'photo': 'https://example.invalid/photo.jpg',
        }
        profile_to = {
            'username': 'man',
            'first_name': 'Man',
            'is_active': True,
            'did_meet': True,
            'gender': 'm',
            'tg_data': [{'tg_uid': 3003}],
        }
        fake_bot = FakeBot()
        self.handler_sympas.bot = fake_bot

        with mock.patch.object(
            self.handler_sympas.Common,
            'check_common_callback',
            mock.AsyncMock(return_value=(profile_from, profile_to, 123)),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'get_photo_buffered',
            mock.AsyncMock(return_value=None),
        ), mock.patch.object(
            self.handler_sympas.Misc,
            'remove_n_send_message',
            mock.AsyncMock(),
        ) as remove_n_send_message:
            await self.handler_sympas.cbq_get_sympa_send_profile(callback, state)

        self.assertTrue(callback.answered)
        self.assertEqual(len(fake_bot.sent_messages), 1)
        self.assertIn('t.me/DoveraBot?start=woman', fake_bot.sent_messages[0][1])
        remove_n_send_message.assert_awaited_once()

class OfferRuntimeDeeplinkTests(unittest.TestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.handler_offer = import_fresh('handler_offer')

    def test_offer_deeplink_uses_runtime_bot_username_and_preserves_ref_payload(self):
        self.assertEqual(
            self.handler_offer.Offer.get_deeplink('offer-uuid', 'sender-ref'),
            't.me/DoveraBot?start=offer-offer-uuid-userId-sender-ref',
        )

if __name__ == '__main__':
    unittest.main()
