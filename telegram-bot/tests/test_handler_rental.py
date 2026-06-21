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

    async def test_rent_hub_mentions_owner_listing_command(self):
        message = FakeMessage(text='/rent')
        state = FakeState()

        await self.handler_rental.Rental.cmd_rent(message, state)

        self.assertIn('/rent_my', message.replies[-1].text)
        self.assertIn('/rent_history', message.replies[-1].text)

    async def test_cmd_rent_my_lists_owner_offers_with_controls(self):
        message = FakeMessage(text='/rent_my')
        state = FakeState()
        response = {
            'offers': [{
                'uuid': 'offer-uuid',
                'title': 'Travel tent',
                'status': 'active',
                'price_text': '500 руб/день',
                'latitude': 55.75,
                'longitude': 37.61,
                'owner': {'uuid': 'requester-uuid'},
            }],
        }

        with mock.patch.object(
            self.handler_rental.Rental,
            'list_owner_offers',
            mock.AsyncMock(return_value=(200, response)),
        ) as list_owner_offers:
            await self.handler_rental.Rental.cmd_rent_my(message, state)

        list_owner_offers.assert_awaited_once_with(
            {'uuid': 'requester-uuid', 'first_name': 'Requester'},
            status_filter='all',
        )
        self.assertIn('Travel tent', message.replies[-1].text)
        buttons = [
            button
            for row in message.replies[-1].reply_markup.inline_keyboard
            for button in row
        ]
        self.assertIn('Пауза', [button.text for button in buttons])
        self.assertIn('В архив', [button.text for button in buttons])
        self.assertIn('На карте', [button.text for button in buttons])

    async def test_cmd_rent_history_lists_open_and_closed_reservations_with_audit(self):
        message = FakeMessage(text='/rent_history')
        state = FakeState()
        open_response = {
            'reservations': [{
                'viewer_role': 'requester',
                'reservation': {
                    'id': 44,
                    'sequence_number': 3,
                    'status': 'awaiting_payment',
                    'date_from': '2026-07-01',
                    'date_to': '2026-07-03',
                },
                'offer': {'uuid': 'offer-uuid', 'title': 'Travel tent'},
                'owner': {'first_name': 'Owner'},
                'events': [{
                    'event_type': 'created',
                    'status_to': 'awaiting_payment',
                }],
                'payment_proofs': [],
            }],
        }
        closed_response = {
            'reservations': [{
                'viewer_role': 'owner',
                'reservation': {
                    'id': 45,
                    'sequence_number': 4,
                    'status': 'confirmed',
                    'date_from': '2026-08-01',
                    'date_to': '2026-08-02',
                },
                'offer': {'uuid': 'offer-uuid-2', 'title': 'Snowboard'},
                'requester': {'first_name': 'Requester'},
                'events': [{
                    'event_type': 'owner_confirm',
                    'status_to': 'confirmed',
                }],
                'payment_proofs': [{
                    'id': 1,
                    'uuid_pack': '00000000-0000-0000-0000-000000000003',
                    'messages': [{'file_type': 'photo'}],
                }],
            }],
        }

        with mock.patch.object(
            self.handler_rental.Rental,
            'list_reservations',
            mock.AsyncMock(side_effect=[(200, open_response), (200, closed_response)]),
        ) as list_reservations:
            await self.handler_rental.Rental.cmd_rent_history(message, state)

        self.assertEqual(list_reservations.await_count, 2)
        list_reservations.assert_any_await(
            {'uuid': 'requester-uuid', 'first_name': 'Requester'},
            status_group='open',
        )
        list_reservations.assert_any_await(
            {'uuid': 'requester-uuid', 'first_name': 'Requester'},
            status_group='recent_closed',
        )
        self.assertEqual(message.replies[0].text, 'Активные брони')
        self.assertIn('Travel tent', message.replies[1].text)
        self.assertIn('События: создана -> ожидает подтверждения оплаты', message.replies[1].text)
        open_buttons = [
            button
            for row in message.replies[1].reply_markup.inline_keyboard
            for button in row
        ]
        self.assertIn('Отправить чек', [button.text for button in open_buttons])
        self.assertEqual(message.replies[2].text, 'Недавно закрытые брони')
        self.assertIn('Подтверждения: 00000000 (photo)', message.replies[3].text)
        self.assertIsNone(message.replies[3].reply_markup)

    async def test_owner_history_card_renders_available_accept_button(self):
        markup = self.handler_rental.Rental.reservation_history_markup({
            'viewer_role': 'owner',
            'reservation': {
                'id': 44,
                'status': 'awaiting_payment',
            },
        })

        buttons = [
            button
            for row in markup.inline_keyboard
            for button in row
        ]
        self.assertIn('Принять', [button.text for button in buttons])

    async def test_owner_markup_includes_reject_payment_proof_button(self):
        markup = self.handler_rental.Rental.markup_reservation_owner({
            'id': 44,
            'status': 'payment_proof_submitted',
        })

        buttons = [
            button
            for row in markup.inline_keyboard
            for button in row
        ]
        reject_buttons = [button for button in buttons if button.text == 'Отклонить чек']
        self.assertEqual(len(reject_buttons), 1)
        self.assertEqual(reject_buttons[0].callback_data, '83~payment_proof_rejected~44')

    async def test_owner_reject_payment_proof_callback_notifies_requester(self):
        callback = FakeCallback('83~payment_proof_rejected~44')
        state = FakeState()
        self.handler_rental.bot = FakeBot()
        response = {
            'reservation': {
                'id': 44,
                'sequence_number': 2,
                'status': 'cancelled',
                'recipient_kind': 'owner',
            },
            'event': {
                'actor_role': 'owner',
                'event_type': 'payment_proof_rejected',
            },
            'offer': {'uuid': 'offer-uuid', 'title': 'Travel tent'},
            'owner': {'first_name': 'Owner'},
            'requester': {
                'first_name': 'Requester',
                'tg_data': [{'tg_uid': 3003}],
            },
        }

        with mock.patch.object(
            self.handler_rental.Misc,
            'post_tg_user',
            mock.AsyncMock(return_value=(200, {'uuid': 'owner-uuid', 'first_name': 'Owner'})),
        ), mock.patch.object(
            self.handler_rental.Rental,
            'reservation_action',
            mock.AsyncMock(return_value=(200, response)),
        ) as reservation_action:
            await self.handler_rental.cbq_rental_reservation_action(callback, state)

        reservation_action.assert_awaited_once_with(
            '44',
            {'uuid': 'owner-uuid', 'first_name': 'Owner'},
            'payment_proof_rejected',
        )
        self.assertTrue(callback.answered)
        self.assertIn('Подтверждение оплаты отклонено', callback.message.replies[-1].text)
        self.assertEqual(len(self.handler_rental.bot.sent_messages), 1)
        self.assertIn('Владелец отклонил подтверждение оплаты', self.handler_rental.bot.sent_messages[0][1])
        self.assertIn('Доверие и недоверие не меняются автоматически', self.handler_rental.bot.sent_messages[0][1])

    async def test_owner_pause_callback_updates_offer_and_renders_resume_controls(self):
        callback = FakeCallback('84~pause~offer-uuid')
        state = FakeState()
        response = {
            'offer': {
                'uuid': 'offer-uuid',
                'title': 'Travel tent',
                'status': 'paused',
                'owner': {'uuid': 'requester-uuid'},
            },
        }

        with mock.patch.object(
            self.handler_rental.Rental,
            'set_owner_offer_status',
            mock.AsyncMock(return_value=(200, response)),
        ) as set_owner_offer_status:
            await self.handler_rental.cbq_rental_owner_action(callback, state)

        set_owner_offer_status.assert_awaited_once_with(
            'offer-uuid',
            {'uuid': 'requester-uuid', 'first_name': 'Requester'},
            'paused',
        )
        self.assertTrue(callback.answered)
        self.assertEqual(callback.answer_text, 'Статус обновлен')
        self.assertIn('на паузе', callback.message.replies[-1].text)
        buttons = [
            button
            for row in callback.message.replies[-1].reply_markup.inline_keyboard
            for button in row
        ]
        self.assertIn('Возобновить', [button.text for button in buttons])

    async def test_stale_owner_callback_shows_notice_and_skips_api(self):
        callback = FakeCallback('84~pause~')
        state = FakeState()

        with mock.patch.object(
            self.handler_rental.Rental,
            'set_owner_offer_status',
            mock.AsyncMock(),
        ) as set_owner_offer_status:
            await self.handler_rental.cbq_rental_owner_action(callback, state)

        set_owner_offer_status.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

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

    async def test_reservation_text_uses_hold_seconds_from_api_payload(self):
        text = self.handler_rental.Rental.text_reservation({
            'reservation': {
                'id': 11,
                'sequence_number': 1,
                'status': 'awaiting_payment',
                'recipient_kind': 'owner',
                'hold_seconds': 1800,
                'hold_seconds_remaining': 60,
            },
            'offer': {'uuid': 'offer-uuid', 'title': 'Travel tent'},
        })

        self.assertIn('Интервал удерживается 30 мин.', text)

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
