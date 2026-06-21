import types
import unittest
from unittest import mock

from bot_test_harness import (
    ContentTypeStub,
    FakeBot,
    FakeCallback,
    FakeMessage,
    FakeState,
    import_fresh,
    install_dependency_stubs,
)


class RentalHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs()
        self.handler_rental = import_fresh('handler_rental')

    async def test_rental_deeplink_uses_runtime_bot_username(self):
        self.assertEqual(
            self.handler_rental.Rental.get_deeplink('offer-uuid'),
            'https://t.me/DoveraBot?start=rent-offer-uuid',
        )

    async def test_stt_file_id_contract_payload_and_parser(self):
        voice = types.SimpleNamespace(file_id='voice-file-id', duration=7, mime_type='audio/ogg')
        message = FakeMessage(content_type=ContentTypeStub.VOICE)
        message.voice = voice

        kwargs = await self.handler_rental.Rental.stt_request_kwargs(message)

        self.assertEqual(kwargs['json']['contract'], 'organizm_hermes_v1')
        self.assertEqual(kwargs['json']['source'], 'telegram_voice')
        self.assertEqual(kwargs['json']['file_id'], 'voice-file-id')
        self.assertEqual(kwargs['json']['telegram_user_id'], 1001)
        self.assertEqual(kwargs['json']['language'], 'ru')
        self.assertEqual(
            self.handler_rental.Rental.stt_transcript_from_response({'result': {'text': 'палатка'}}),
            'палатка',
        )

    async def test_markup_offer_includes_show_on_map_link(self):
        markup = self.handler_rental.Rental.markup_offer(
            {'uuid': 'viewer-uuid'},
            {
                'uuid': 'offer-uuid',
                'title': 'Travel tent',
                'latitude': 55.75,
                'longitude': 37.61,
                'owner': {'uuid': 'owner-uuid'},
            },
        )

        buttons = [button for row in markup.inline_keyboard for button in row]
        map_buttons = [button for button in buttons if button.text == 'На карте']
        self.assertEqual(len(map_buttons), 1)
        self.assertIn('rental=on', map_buttons[0].url)
        self.assertIn('rental_uuid=offer-uuid', map_buttons[0].url)

    async def test_process_rental_search_stops_on_command_interrupt(self):
        message = FakeMessage(text='/rent')
        state = FakeState()

        with mock.patch.object(self.handler_rental, 'is_it_command', mock.AsyncMock(return_value=True)), \
             mock.patch.object(
                 self.handler_rental.Rental,
                 'message_or_voice_text',
                 mock.AsyncMock(return_value='tent'),
             ) as message_or_voice_text:
            await self.handler_rental.process_rental_search(message, state)

        message_or_voice_text.assert_not_awaited()

    async def test_inline_rental_search_smoke_uses_date_params_and_reports_empty(self):
        message = FakeMessage(text='/rent_search tent 2026-07-01 москва')
        state = FakeState()

        with mock.patch.object(
            self.handler_rental.Rental,
            'search_with_params',
            mock.AsyncMock(return_value=(200, {'offers': []})),
        ) as search_with_params:
            await self.handler_rental.Rental.cmd_rent_search(message, state)

        search_with_params.assert_awaited_once_with(
            'tent 2026-07-01 москва',
            'requester-uuid',
            date_from='2026-07-01',
            date_to='',
        )
        self.assertTrue(state.cleared)
        self.assertEqual(message.replies[-1].text, 'Ничего не найдено')

    async def test_payment_reported_callback_enters_payment_proof_state(self):
        state = FakeState()
        callback = FakeCallback('83~payment_reported~44')

        await self.handler_rental.cbq_rental_reservation_action(callback, state)

        self.assertIs(state.state, self.handler_rental.FSMRentalPaymentProof.ask)
        self.assertEqual(state.data['reservation_id'], '44')
        self.assertTrue(state.data['uuid_pack'])
        self.assertTrue(callback.answered)
        self.assertIn('подтверждение оплаты', callback.message.replies[0].text)

    async def test_stale_reservation_callback_shows_notice_and_skips_state(self):
        state = FakeState()
        callback = FakeCallback('83~payment_reported~not-a-number')

        await self.handler_rental.cbq_rental_reservation_action(callback, state)

        self.assertIsNone(state.state)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_unknown_reservation_action_shows_notice(self):
        state = FakeState()
        callback = FakeCallback('83~archive~44')

        with mock.patch.object(
            self.handler_rental.Rental,
            'reservation_action',
            mock.AsyncMock(),
        ) as reservation_action:
            await self.handler_rental.cbq_rental_reservation_action(callback, state)

        reservation_action.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_stale_booking_callback_shows_notice_and_skips_api(self):
        callback = FakeCallback('82~')
        state = FakeState()

        with mock.patch.object(
            self.handler_rental.Rental,
            'reserve',
            mock.AsyncMock(),
        ) as reserve:
            await self.handler_rental.cbq_rental_book(callback, state)

        reserve.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_contact_callback_auth_failure_shows_notice(self):
        callback = FakeCallback('81~offer-uuid')
        state = FakeState()

        with mock.patch.object(
            self.handler_rental.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(500, {})),
        ):
            await self.handler_rental.cbq_rental_contact(callback, state)

        self.assertIsNone(state.state)
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

    async def test_booking_reports_owner_notification_failure(self):
        callback = FakeCallback('82~offer-uuid')
        state = FakeState()
        self.handler_rental.bot = FakeBot(fail_send=True)
        response = {
            'reservation': {
                'id': 11,
                'sequence_number': 1,
                'status': 'awaiting_payment',
                'recipient_kind': 'owner',
                'hold_seconds_remaining': 600,
            },
            'offer': {'uuid': 'offer-uuid', 'title': 'Travel tent'},
            'owner': {'tg_data': [{'tg_uid': 3003}], 'username': 'owner'},
        }

        with mock.patch.object(
            self.handler_rental.Rental,
            'reserve',
            mock.AsyncMock(return_value=(200, response)),
        ), mock.patch.object(
            self.handler_rental.Rental,
            'register_message',
            mock.AsyncMock(return_value=(200, {})),
        ):
            await self.handler_rental.cbq_rental_book(callback, state)

        self.assertTrue(callback.answered)
        self.assertTrue(any('владельцу не удалось' in reply.text for reply in callback.message.replies))

    async def test_booking_success_registers_prompt_and_notifies_owner(self):
        callback = FakeCallback('82~offer-uuid')
        state = FakeState()
        self.handler_rental.bot = FakeBot()
        response = {
            'reservation': {
                'id': 11,
                'sequence_number': 1,
                'status': 'awaiting_payment',
                'recipient_kind': 'owner',
                'hold_seconds_remaining': 600,
                'recipient_payment_info_snapshot': 'owner bank',
            },
            'offer': {'uuid': 'offer-uuid', 'title': 'Travel tent'},
            'owner': {'tg_data': [{'tg_uid': 3003}], 'username': 'owner'},
        }

        with mock.patch.object(
            self.handler_rental.Rental,
            'reserve',
            mock.AsyncMock(return_value=(200, response)),
        ), mock.patch.object(
            self.handler_rental.Rental,
            'register_message',
            mock.AsyncMock(return_value=(200, {})),
        ) as register_message:
            await self.handler_rental.cbq_rental_book(callback, state)

        self.assertTrue(callback.answered)
        self.assertIn('Заявка на бронь №1 создана', callback.message.replies[0].text)
        register_message.assert_awaited_once_with(
            'offer-uuid',
            'booking_prompt',
            callback.message.chat.id,
            callback.message.replies[0].message_id,
            recipient_uuid='requester-uuid',
        )
        self.assertEqual(len(self.handler_rental.bot.sent_messages), 1)
        self.assertEqual(self.handler_rental.bot.sent_messages[0][0], 3003)
        self.assertIn('Заявка на бронь №1', self.handler_rental.bot.sent_messages[0][1])

    async def test_payment_proof_success_forwards_pack_notifies_owner_and_clears_state(self):
        message = FakeMessage(text='paid')
        state = FakeState({
            'user_uuid': 'requester-uuid',
            'reservation_id': '44',
            'uuid_pack': 'proof-pack',
        })
        self.handler_rental.bot = FakeBot()
        response = {
            'reservation': {
                'id': 44,
                'sequence_number': 2,
                'status': 'payment_proof_submitted',
                'recipient_kind': 'owner',
            },
            'offer': {'uuid': 'offer-uuid', 'title': 'Travel tent'},
            'owner': {'tg_data': [{'tg_uid': 3003}], 'username': 'owner'},
        }

        with mock.patch.object(
            self.handler_rental.Rental,
            'payment_proof',
            mock.AsyncMock(return_value=(200, response)),
        ) as payment_proof, mock.patch.object(
            self.handler_rental.Misc,
            'api_request',
            mock.AsyncMock(return_value=(200, {})),
            create=True,
        ) as api_request:
            await self.handler_rental.process_rental_payment_proof(message, state)

        payment_proof.assert_awaited_once_with(
            '44',
            {'uuid': 'requester-uuid', 'first_name': 'Requester'},
            message,
            'proof-pack',
        )
        api_request.assert_awaited_once()
        self.assertEqual(api_request.await_args.kwargs['path'], '/api/show_tgmsg_pack')
        self.assertEqual(api_request.await_args.kwargs['json']['uuid_pack'], 'proof-pack')
        self.assertTrue(state.cleared)
        self.assertEqual(len(self.handler_rental.bot.sent_messages), 1)
        self.assertIn('Получено подтверждение оплаты', self.handler_rental.bot.sent_messages[0][1])
        self.assertIn('Подтверждение получено', message.replies[-1].text)

if __name__ == '__main__':
    unittest.main()
