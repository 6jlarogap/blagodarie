import types
import unittest

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
