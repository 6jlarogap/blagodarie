import types
import unittest
from unittest import mock

from bot_test_harness import (
    FakeCallback,
    import_fresh,
    install_dependency_stubs,
)


class CommonRuntimeDeeplinkTests(unittest.TestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')

    def test_start_deeplink_uses_runtime_username_and_preserves_payload(self):
        self.assertEqual(
            self.common.Misc.get_start_deeplink('meet'),
            't.me/DoveraBot?start=meet',
        )
        self.assertEqual(
            self.common.Misc.get_start_deeplink('m-meet-token', https=True),
            'https://t.me/DoveraBot?start=m-meet-token',
        )
        self.assertEqual(
            self.common.Misc.get_deeplink({'username': 'woman'}),
            't.me/DoveraBot?start=woman',
        )

    def test_private_mini_app_launcher_and_login_url_fallback_are_explicit(self):
        mini = self.common.Misc.make_launch_button(
            'Схема', 'https://graph.example/?user_trusts=alice', use_mini_app=True,
            keep_user_data='on',
        )
        self.assertNotIn('login_url', mini.kwargs)
        self.assertEqual(
            mini.kwargs['web_app']['url'],
            'https://graph.example/?user_trusts=alice&mini_app=1',
        )
        fallback = self.common.Misc.make_launch_button(
            'Схема', 'https://graph.example/?user_trusts=alice', use_mini_app=False,
            keep_user_data='on',
        )
        self.assertNotIn('web_app', fallback.kwargs)
        self.assertIn('login_url', fallback.kwargs)


class PendingProfileCardTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')

    async def test_pending_card_is_labelled_and_has_no_message_actions(self):
        sender = {
            'user_id': 1, 'uuid': 'sender-uuid', 'did_meet': None,
            'r_sympa_username': None,
        }
        pending = {
            'user_id': 2, 'uuid': 'target-uuid', 'username': 'targetsid1',
            'first_name': '@pending_name', 'comment': '', 'is_org': True,
            'subject_kind': 'unknown', 'is_person': False,
            'gender': None, 'trust_count': 0, 'sum_thanks_count': 0,
            'acq_count': 0, 'mistrust_count': 0, 'invite_meet_count': 0,
            'did_meet': None, 'owner': {}, 'tg_data': [], 'keys': [],
            'pending_tg_username': 'pending_name', 'is_active': False,
            'is_power': False, 'latitude': None, 'longitude': None,
        }
        tg_user = types.SimpleNamespace(id=1001)
        self.common.bot_data.id = 9999

        with mock.patch.object(
            self.common.Misc,
            'call_response_relations',
            mock.AsyncMock(return_value=(200, {
                'from_to': {'attitude': self.common.Attitude.TRUST, 'is_sympa_confirmed': False},
                'to_from': {'attitude': None, 'is_sympa_confirmed': False},
            })),
        ), mock.patch.object(
            self.common.Misc,
            'send_or_edit_card',
            mock.AsyncMock(),
        ) as send_card:
            await self.common.Misc.show_card(pending, sender, tg_user)

        reply, markup = send_card.await_args.args[:2]
        labels = [button.text for row in markup.inline_keyboard for button in row]
        self.assertIn('Неподтверждённое имя Telegram: @pending_name', reply)
        self.assertNotIn('Написать', labels)
        self.assertNotIn('Архив', labels)
        self.assertNotIn('Знакомы', labels)
        self.assertTrue(all(button is not None for row in markup.inline_keyboard for button in row))

        pending.update(
            pending_tg_username=None,
            subject_kind='bot',
            is_person=False,
            tg_data=[{'tg_uid': '2', 'tg_username': 'helper_bot'}],
        )
        with mock.patch.object(
            self.common.Misc,
            'call_response_relations',
            mock.AsyncMock(return_value=(200, {
                'from_to': {'attitude': None, 'is_sympa_confirmed': False},
                'to_from': {'attitude': None, 'is_sympa_confirmed': False},
            })),
        ), mock.patch.object(self.common.Misc, 'send_or_edit_card', send_card):
            await self.common.Misc.show_card(pending, sender, tg_user)
        markup = send_card.await_args.args[1]
        labels = [button.text for row in markup.inline_keyboard for button in row]
        self.assertNotIn('Написать', labels)
        self.assertNotIn('Архив', labels)
        self.assertNotIn('Знакомы', labels)

class CommonCallbackParserTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')

    async def test_callback_parts_and_notice(self):
        callback = FakeCallback('44~offer-uuid~2~referrer')

        self.assertEqual(
            self.common.Misc.parse_callback_data(
                callback,
                self.common.KeyboardType.OFFER_ANSWER,
                min_parts=3,
            ),
            ['44', 'offer-uuid', '2', 'referrer'],
        )
        self.assertEqual(self.common.Misc.callback_int_part(callback, 2), 2)

        await self.common.Misc.answer_callback_notice(callback)

        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    def test_get_sid_from_callback_validates_payload(self):
        valid = FakeCallback('65~abcdefghij~targetuser1~123')
        invalid = FakeCallback('65~not-valid~targetuser1~123')

        self.assertEqual(self.common.Misc.get_sid_from_callback(valid), 'abcdefghij')
        self.assertIsNone(self.common.Misc.get_sid_from_callback(invalid))

class LegacyMediaPackTests(unittest.TestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')

    def test_tgdesc_uses_largest_photo_from_media_pack(self):
        message = types.SimpleNamespace(
            message_id=11,
            chat=types.SimpleNamespace(id=22),
            media_group_id='pack-1',
            caption='caption',
            photo=[
                types.SimpleNamespace(file_id='small-photo'),
                types.SimpleNamespace(file_id='large-photo'),
            ],
            audio=None,
            video=None,
            document=None,
            voice=None,
        )

        desc = self.common.TgDesc.from_message(message, 'uuid-pack')

        self.assertEqual(desc['message_id'], 11)
        self.assertEqual(desc['chat_id'], 22)
        self.assertEqual(desc['media_group_id'], 'pack-1')
        self.assertEqual(desc['caption'], 'caption')
        self.assertEqual(desc['file_type'], 'photo')
        self.assertEqual(desc['file_id'], 'large-photo')
        self.assertEqual(desc['uuid_pack'], 'uuid-pack')

    def test_tgdesc_records_voice_file_when_no_photo(self):
        message = types.SimpleNamespace(
            message_id=12,
            chat=types.SimpleNamespace(id=23),
            media_group_id='',
            caption='',
            photo=None,
            audio=None,
            video=None,
            document=None,
            voice=types.SimpleNamespace(file_id='voice-file'),
        )

        desc = self.common.TgDesc.from_message(message, 'uuid-pack')

        self.assertEqual(desc['file_type'], 'voice')
        self.assertEqual(desc['file_id'], 'voice-file')

if __name__ == '__main__':
    unittest.main()
