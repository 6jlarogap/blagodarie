# handler_rental.py
#
# Команды и сообщения для проката снаряжения.

import re
import datetime
from uuid import uuid4

import aiohttp
from aiogram import Router, F, html
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from handler_bot import is_it_command

import logging
import settings

from common import Misc, KeyboardType, Rcache, TgDesc
import me
dp, bot, bot_data = me.dp, me.bot, me.bot_data

router = Router()


class FSMRentalOffer(StatesGroup):
    ask = State()


class FSMRentalSearch(StatesGroup):
    ask = State()


class FSMRentalContact(StatesGroup):
    ask = State()


class FSMRentalPaymentProof(StatesGroup):
    ask = State()


class Rental(object):

    PROMPT_OFFER = (
        'Опишите, что сдаёте в прокат: предмет, где забрать, когда доступно, '
        'цена и важные условия. Можно прислать текст, фото с подписью, видео, документ или голосовое.'
    )
    PROMPT_SEARCH = 'Что ищем в прокат? Укажите предмет, место или даты одним сообщением.'
    PROMPT_SEARCH_CONTEXT = 'Где или на какие даты искать? Можно ответить голосом.'

    ACTION_OWNER_ACCEPT = 'owner_accept'
    ACTION_PAYMENT_REPORTED = 'payment_reported'
    ACTION_OWNER_CONFIRM = 'owner_confirm'
    ACTION_CANCEL = 'cancel'

    STATUS_LABELS = {
        'sent': 'заявка отправлена',
        'awaiting_payment': 'ожидает подтверждения оплаты',
        'owner_accepted': 'владелец принял заявку',
        'payment_reported': 'оплата отмечена',
        'payment_proof_submitted': 'подтверждение оплаты отправлено',
        'confirmed': 'бронь подтверждена',
        'cancelled': 'заявка отменена',
        'expired': 'время удержания истекло',
    }

    @classmethod
    def message_text(cls, message):
        return (message.text or message.caption or '').strip()

    @classmethod
    def get_deeplink(cls, offer_uuid):
        return f'https://t.me/{bot_data.username}?start=rent-{offer_uuid}'

    @classmethod
    async def voice_transcript(cls, message):
        url = getattr(settings, 'RENTAL_STT_URL', '')
        if not url or not message.voice:
            return ''
        headers = {}
        if getattr(settings, 'RENTAL_STT_TOKEN', ''):
            headers['Authorization'] = 'Bearer %s' % settings.RENTAL_STT_TOKEN
        timeout = aiohttp.ClientTimeout(total=getattr(settings, 'HTTP_TIMEOUT', 60))
        mode = getattr(settings, 'RENTAL_STT_MODE', 'file_id')
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if mode == 'download':
                    form = aiohttp.FormData()
                    form.add_field('file_id', message.voice.file_id)
                    form.add_field('telegram_user_id', str(message.from_user.id))
                    form.add_field('voice', await Misc.get_file_bytes(message.voice),
                                   filename='voice.ogg',
                                   content_type=message.voice.mime_type or 'audio/ogg')
                    request_kwargs = dict(data=form)
                else:
                    request_kwargs = dict(json=dict(
                        file_id=message.voice.file_id,
                        duration=message.voice.duration,
                        mime_type=message.voice.mime_type or '',
                        telegram_user_id=message.from_user.id,
                    ))
                async with session.post(url, headers=headers, **request_kwargs) as resp:
                    if resp.status >= 400:
                        logging.warning('rental STT failed with status %s', resp.status)
                        return ''
                    try:
                        data = await resp.json(content_type=None)
                    except (ValueError, aiohttp.ContentTypeError):
                        return (await resp.text()).strip()
        except Exception:
            logging.exception('rental STT request failed')
            return ''
        if isinstance(data, dict):
            result = data.get('transcript') or data.get('text') or ''
            if not result and isinstance(data.get('result'), dict):
                result = data['result'].get('transcript') or data['result'].get('text') or ''
            return str(result).strip()
        return ''

    @classmethod
    async def message_or_voice_text(cls, message, allow_voice_placeholder=False):
        text = cls.message_text(message)
        if text:
            return text
        if message.content_type == ContentType.VOICE:
            transcript = await cls.voice_transcript(message)
            if transcript:
                return transcript
            if allow_voice_placeholder:
                return 'Голосовое описание. Текст распознавания добавляется внешним STT.'
        return ''

    @classmethod
    def extract_slots(cls, text):
        title = ''
        for line in text.split('\n'):
            line = line.strip()
            if line:
                title = line[:120]
                break
        price_text = ''
        if m := re.search(r'((?:\d[\d\s\.,]*)\s*(?:руб\.?|р\.?|₽|usd|eur|byn|долл\.?)[^\n]*)', text, flags=re.I):
            price_text = m.group(1).strip()
        address = ''
        if m := re.search(r'(?:адрес|где|место)\s*[:\-]\s*([^\n]+)', text, flags=re.I):
            address = m.group(1).strip()
        latitude, longitude = Misc.check_location_str(text)
        return dict(
            title=title,
            item_text=title,
            description_text=text,
            price_text=price_text,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )

    @classmethod
    def parse_search_date(cls, raw):
        raw = (raw or '').strip()
        for date_format in ('%Y-%m-%d', '%d.%m.%Y'):
            try:
                return datetime.datetime.strptime(raw, date_format).date().isoformat()
            except ValueError:
                pass
        return ''

    @classmethod
    def extract_search_slots(cls, text):
        date_values = [
            cls.parse_search_date(value)
            for value in re.findall(r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{4})\b', text)
        ]
        date_values = [value for value in date_values if value]
        latitude, longitude = Misc.check_location_str(text)
        has_context = bool(date_values or latitude is not None or re.search(
            r'\b(адрес|где|место|город|метро|улица|рядом|москва|минск|сочи|спб|санкт-петербург)\b',
            text,
            flags=re.I,
        ))
        return dict(
            query=text.strip(),
            date_from=date_values[0] if date_values else '',
            date_to=date_values[-1] if len(date_values) > 1 else '',
            has_context=has_context,
        )

    @classmethod
    async def cmd_rent(cls, message: Message, state: FSMContext):
        await message.reply(
            'Прокат снаряжения:\n'
            '/rent_offer - создать объявление\n'
            '/rent_search - найти снаряжение'
        )

    @classmethod
    async def cmd_rent_offer(cls, message: Message, state: FSMContext):
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        await state.set_state(FSMRentalOffer.ask)
        await state.update_data(
            user_uuid=response_sender['uuid'],
            uuid_pack=str(uuid4()),
        )
        await message.reply(cls.PROMPT_OFFER, reply_markup=Misc.reply_markup_cancel_row())

    @classmethod
    async def cmd_rent_search(cls, message: Message, state: FSMContext):
        query = re.sub(r'^\s*/rent_search(?:@\w+)?\s*', '', message.text or '', flags=re.I).strip()
        if query:
            await state.set_state(FSMRentalSearch.ask)
            await cls.handle_search_text(message, state, query)
            return
        await state.set_state(FSMRentalSearch.ask)
        await message.reply(cls.PROMPT_SEARCH, reply_markup=Misc.reply_markup_cancel_row())

    @classmethod
    async def create_offer(cls, payload):
        payload.update(tg_token=settings.TOKEN)
        logging.debug('create rental offer, payload: %s' % Misc.secret(payload))
        status, response = await Misc.api_request(
            path='/api/rental/offer',
            method='post',
            json=payload,
        )
        logging.debug('create rental offer, status: %s' % status)
        logging.debug('create rental offer, response: %s' % response)
        return status, response

    @classmethod
    async def put_offer(cls, payload):
        payload.update(tg_token=settings.TOKEN)
        logging.debug('put rental offer, payload: %s' % Misc.secret(payload))
        status, response = await Misc.api_request(
            path='/api/rental/offer',
            method='put',
            json=payload,
        )
        logging.debug('put rental offer, status: %s' % status)
        logging.debug('put rental offer, response: %s' % response)
        return status, response

    @classmethod
    async def get_offer(cls, offer_uuid, user_uuid=None, include_payment=True):
        params = dict(uuid=offer_uuid)
        if user_uuid:
            params.update(user_uuid=user_uuid)
        if include_payment:
            params.update(include_payment='on')
        status, response = await Misc.api_request(
            path='/api/rental/offer',
            method='get',
            params=params,
        )
        return status, response

    @classmethod
    async def search(cls, query, user_uuid):
        params = dict(query=query, user_uuid=user_uuid, number=5)
        status, response = await Misc.api_request(
            path='/api/rental/search',
            method='get',
            params=params,
        )
        return status, response

    @classmethod
    async def search_with_params(cls, query, user_uuid, date_from='', date_to=''):
        params = dict(query=query, user_uuid=user_uuid, number=5)
        if date_from:
            params.update(date_from=date_from)
        if date_to:
            params.update(date_to=date_to)
        status, response = await Misc.api_request(
            path='/api/rental/search',
            method='get',
            params=params,
        )
        return status, response

    @classmethod
    async def register_message(cls, offer_uuid, message_kind, chat_id, message_id, recipient_uuid=''):
        payload = dict(
            tg_token=settings.TOKEN,
            offer_uuid=offer_uuid,
            message_kind=message_kind,
            chat_id=chat_id,
            message_id=message_id,
        )
        if recipient_uuid:
            payload.update(recipient_uuid=recipient_uuid)
        status, response = await Misc.api_request(
            path='/api/rental/message',
            method='post',
            json=payload,
        )
        if status != 200:
            logging.warning('rental message registration failed: %s %s', status, response)
        return status, response

    @classmethod
    async def reserve(cls, offer_uuid, profile_from, source_message=None):
        payload = dict(
            tg_token=settings.TOKEN,
            user_uuid=profile_from['uuid'],
            offer_uuid=offer_uuid,
        )
        if source_message:
            payload.update(
                source_chat_id=source_message.chat.id,
                source_message_id=source_message.message_id,
            )
        status, response = await Misc.api_request(
            path='/api/rental/reservation',
            method='post',
            json=payload,
        )
        return status, response

    @classmethod
    async def reservation_action(cls, reservation_id, profile_from, action):
        payload = dict(
            tg_token=settings.TOKEN,
            user_uuid=profile_from['uuid'],
            reservation_id=reservation_id,
            action=action,
        )
        status, response = await Misc.api_request(
            path='/api/rental/reservation',
            method='put',
            json=payload,
        )
        return status, response

    @classmethod
    async def payment_proof(cls, reservation_id, profile_from, message, uuid_pack):
        payload = dict(
            tg_token=settings.TOKEN,
            user_uuid=profile_from['uuid'],
            reservation_id=reservation_id,
            tgdesc=TgDesc.from_message(message, uuid_pack),
        )
        status, response = await Misc.api_request(
            path='/api/rental/reservation/payment_proof',
            method='post',
            json=payload,
        )
        return status, response

    @classmethod
    async def contact(cls, offer_uuid, profile_from, text):
        payload = dict(
            tg_token=settings.TOKEN,
            user_uuid=profile_from['uuid'],
            offer_uuid=offer_uuid,
            message=text,
        )
        status, response = await Misc.api_request(
            path='/api/rental/contact',
            method='post',
            json=payload,
        )
        return status, response

    @classmethod
    def text_offer(cls, offer):
        result = '<b>%s</b>\n' % html.quote(offer.get('title') or offer.get('item_text') or 'Прокат')
        if offer.get('description_text'):
            result += html.quote(offer['description_text']) + '\n'
        if offer.get('availability_text') or offer.get('available_from') or offer.get('available_to'):
            availability = offer.get('availability_text') or ''
            if offer.get('available_from') or offer.get('available_to'):
                availability += ' %s - %s' % (offer.get('available_from') or '?', offer.get('available_to') or '?')
            result += '\nДоступность: %s\n' % html.quote(availability.strip())
        if offer.get('price_text'):
            result += '\nЦена: %s\n' % html.quote(offer['price_text'])
        elif offer.get('price_amount'):
            result += '\nЦена: %s %s %s\n' % (
                html.quote(offer.get('price_amount') or ''),
                html.quote(offer.get('price_currency') or ''),
                html.quote(offer.get('price_period') or ''),
            )
        if offer.get('address'):
            result += '\nАдрес: %s\n' % html.quote(offer['address'])
        badges = offer.get('trust_badges') or {}
        result += '\nВладелец: %s' % Misc.get_deeplink_with_name(offer['owner'])
        if badges:
            result += ' (%s доверий, %s знакомств)' % (
                badges.get('owner_trust_count', 0),
                badges.get('owner_acq_count', 0),
            )
        if offer.get('payment_details'):
            result += '\n\nРеквизиты/условия оплаты:\n%s' % html.quote(offer['payment_details'])
        result += '\n\n%s' % Misc.get_html_a(cls.get_deeplink(offer['uuid']), 'Ссылка на объявление')
        return result

    @classmethod
    def markup_offer(cls, profile_from, offer):
        if profile_from and profile_from.get('uuid') == offer.get('owner', {}).get('uuid'):
            return None
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Забронировать',
                    callback_data='%s%s%s' % (
                        KeyboardType.RENTAL_BOOK,
                        KeyboardType.SEP,
                        offer['uuid'],
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Написать владельцу',
                    callback_data='%s%s%s' % (
                        KeyboardType.RENTAL_CONTACT,
                        KeyboardType.SEP,
                        offer['uuid'],
                    ),
                )
            ],
        ])

    @classmethod
    def reservation_status_label(cls, reservation):
        return cls.STATUS_LABELS.get(
            reservation.get('status'),
            reservation.get('status') or 'статус неизвестен',
        )

    @classmethod
    def reservation_action_callback_data(cls, action, reservation_id):
        return '%s%s%s%s%s' % (
            KeyboardType.RENTAL_RESERVATION_ACTION,
            KeyboardType.SEP,
            action,
            KeyboardType.SEP,
            reservation_id,
        )

    @classmethod
    def markup_reservation_consumer(cls, reservation):
        status = reservation.get('status')
        rows = []
        if status in ('awaiting_payment', 'owner_accepted'):
            rows.append([
                InlineKeyboardButton(
                    text='Отправить чек',
                    callback_data=cls.reservation_action_callback_data(
                        cls.ACTION_PAYMENT_REPORTED,
                        reservation['id'],
                    ),
                )
            ])
        if status in ('sent', 'awaiting_payment', 'owner_accepted', 'payment_proof_submitted'):
            rows.append([
                InlineKeyboardButton(
                    text='Отменить бронь',
                    callback_data=cls.reservation_action_callback_data(
                        cls.ACTION_CANCEL,
                        reservation['id'],
                    ),
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

    @classmethod
    def markup_reservation_owner(cls, reservation):
        status = reservation.get('status')
        rows = []
        if status == 'sent':
            rows.append([
                InlineKeyboardButton(
                    text='Принять',
                    callback_data=cls.reservation_action_callback_data(
                        cls.ACTION_OWNER_ACCEPT,
                        reservation['id'],
                    ),
                )
            ])
        if status in ('payment_reported', 'payment_proof_submitted'):
            rows.append([
                InlineKeyboardButton(
                    text='Подтвердить',
                    callback_data=cls.reservation_action_callback_data(
                        cls.ACTION_OWNER_CONFIRM,
                        reservation['id'],
                    ),
                )
            ])
        if status in ('sent', 'awaiting_payment', 'owner_accepted', 'payment_reported', 'payment_proof_submitted'):
            rows.append([
                InlineKeyboardButton(
                    text='Отменить',
                    callback_data=cls.reservation_action_callback_data(
                        cls.ACTION_CANCEL,
                        reservation['id'],
                    ),
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

    @classmethod
    def canonical_message(cls, offer):
        if offer.get('canonical_message'):
            return offer['canonical_message']
        for message in offer.get('telegram_messages') or []:
            if message.get('message_kind') == 'owner_offer':
                return message
        desc = offer.get('desc') or []
        return desc[0] if desc else None

    @classmethod
    async def show_offer(cls, message, profile_from, offer, message_kind='search_result'):
        reply_markup = cls.markup_offer(profile_from, offer)
        canonical_message = cls.canonical_message(offer)
        if canonical_message and reply_markup:
            try:
                sent = await bot.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=canonical_message['chat_id'],
                    message_id=canonical_message['message_id'],
                    reply_markup=reply_markup,
                )
                await cls.register_message(
                    offer['uuid'],
                    message_kind,
                    message.chat.id,
                    sent.message_id,
                    recipient_uuid=profile_from.get('uuid', '') if profile_from else '',
                )
                return
            except (TelegramBadRequest, TelegramForbiddenError):
                pass
        try:
            sent = await message.reply(
                cls.text_offer(offer),
                reply_markup=reply_markup,
            )
            await cls.register_message(
                offer['uuid'],
                message_kind,
                sent.chat.id,
                sent.message_id,
                recipient_uuid=profile_from.get('uuid', '') if profile_from else '',
            )
        except (TelegramBadRequest, TelegramForbiddenError):
            await message.reply('Объявление показать не удалось')

    @classmethod
    async def send_search_results(cls, message, query, date_from='', date_to=''):
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        status, response = await cls.search_with_params(
            query,
            response_sender['uuid'],
            date_from=date_from,
            date_to=date_to,
        )
        if status != 200:
            await message.reply('Поиск временно недоступен')
            return
        clarification = response.get('clarification')
        if clarification:
            choices = ', '.join(
                choice.get('canonical_name') or choice.get('slug')
                for choice in clarification.get('choices') or []
            )
            await message.reply(
                '%s: %s' % (
                    clarification.get('message') or 'Уточните запрос',
                    choices or 'напишите точнее',
                )
            )
            return
        offers = response.get('offers') or []
        if not offers:
            await message.reply('Ничего не найдено')
            return
        for offer in offers:
            await cls.show_offer(message, response_sender, offer)

    @classmethod
    async def handle_search_text(cls, message, state, text):
        slots = cls.extract_search_slots(text)
        data = await state.get_data()
        query = data.get('query') or slots['query']
        context_text = data.get('context_text') or ''
        date_from = data.get('date_from') or slots['date_from']
        date_to = data.get('date_to') or slots['date_to']
        has_context = bool(data.get('has_context') or slots['has_context'])
        if data.get('query') and slots['query']:
            context_text = ('%s %s' % (context_text, slots['query'])).strip()
        if not query:
            await state.set_state(FSMRentalSearch.ask)
            await message.reply(cls.PROMPT_SEARCH, reply_markup=Misc.reply_markup_cancel_row())
            return
        if not has_context:
            await state.update_data(
                query=query,
                date_from=date_from,
                date_to=date_to,
                has_context=False,
            )
            await message.reply(cls.PROMPT_SEARCH_CONTEXT, reply_markup=Misc.reply_markup_cancel_row())
            return
        await state.clear()
        search_query = ('%s %s' % (query, context_text)).strip()
        await cls.send_search_results(
            message,
            search_query,
            date_from=date_from,
            date_to=date_to,
        )

    @classmethod
    def text_reservation(cls, response):
        reservation = response['reservation']
        offer = response['offer']
        payment = reservation.get('recipient_payment_info_snapshot') or ''
        hold_seconds = reservation.get('hold_seconds_remaining') or 0
        if reservation.get('recipient_kind') == 'system':
            recipient_text = (
                'Получатель платежа: команда проекта. Это каждая 10-я бронь; '
                'дар идет на развитие Doverabot.'
            )
        else:
            recipient_text = 'Получатель платежа: владелец объявления.'
        text = (
            'Заявка на бронь №%s создана.\n\n'
            '%s\n\n'
            '%s'
        ) % (
            reservation.get('sequence_number') or reservation.get('id'),
            html.quote(offer.get('title') or offer.get('item_text') or 'Прокат'),
            recipient_text,
        )
        if hold_seconds:
            minutes = max(1, int((hold_seconds + 59) / 60))
            text += '\n\nИнтервал удерживается %s мин. Пришлите подтверждение оплаты до истечения времени.' % minutes
        if payment:
            text += '\n\nРеквизиты/условия оплаты:\n%s' % html.quote(payment)
        else:
            text += '\n\nРеквизиты не указаны. Договоритесь с владельцем перед оплатой.'
        return text

    @classmethod
    def text_owner_reservation_notice(cls, response, profile_from):
        reservation = response['reservation']
        offer = response['offer']
        recipient = 'системе' if reservation.get('recipient_kind') == 'system' else 'владельцу'
        amount = reservation.get('amount_suggested') or ''
        if amount:
            amount = '%s %s' % (amount, reservation.get('currency') or '')
        dates = 'не указаны'
        if reservation.get('date_from') or reservation.get('date_to'):
            dates = '%s - %s' % (reservation.get('date_from') or '?', reservation.get('date_to') or '?')
        return (
            'Заявка на бронь №%s\n'
            'Объявление: %s\n'
            'От: %s\n'
            'Даты: %s\n'
            'Сумма: %s\n'
            'Реквизиты показаны: %s'
        ) % (
            reservation.get('sequence_number') or reservation.get('id'),
            html.quote(offer.get('title') or offer.get('item_text') or 'Прокат'),
            Misc.get_deeplink_with_name(profile_from),
            html.quote(dates),
            html.quote(amount or 'не указана'),
            recipient,
        )

    @classmethod
    def text_reservation_status(cls, response):
        reservation = response['reservation']
        offer = response['offer']
        return (
            'Заявка на бронь №%s\n'
            'Объявление: %s\n'
            'Статус: %s'
        ) % (
            reservation.get('sequence_number') or reservation.get('id'),
            html.quote(offer.get('title') or offer.get('item_text') or 'Прокат'),
            cls.reservation_status_label(reservation),
        )

    @classmethod
    def text_consumer_reservation_update(cls, response):
        text = cls.text_reservation_status(response)
        reservation = response['reservation']
        if reservation.get('status') == 'owner_accepted':
            text += '\n\nВладелец принял заявку. Если условия подходят, сообщите об оплате кнопкой ниже.'
        elif reservation.get('status') == 'payment_proof_submitted':
            if reservation.get('recipient_kind') == 'system':
                text += '\n\nПодтверждение получено; бронь держится под доверие. Не называйте это проверенной оплатой до аудита.'
            else:
                text += '\n\nПодтверждение получено и передано владельцу.'
        elif reservation.get('status') == 'confirmed':
            text += '\n\nВладелец подтвердил бронь.'
        elif reservation.get('status') == 'cancelled':
            text += '\n\nЗаявка закрыта.'
        elif reservation.get('status') == 'expired':
            text += '\n\nВремя удержания истекло. Создайте новую бронь, если даты еще свободны.'
        return text

    @classmethod
    def text_owner_reservation_update(cls, response, profile_from):
        text = cls.text_reservation_status(response)
        requester = response.get('requester') or {}
        if requester:
            text += '\nОт: %s' % Misc.get_deeplink_with_name(requester)
        reservation = response['reservation']
        if reservation.get('status') in ('payment_reported', 'payment_proof_submitted'):
            if reservation.get('recipient_kind') == 'system':
                text += '\n\nКлиент прислал подтверждение системного платежа. Бронь создана под доверие; подтверждайте выдачу снаряжения, а не проверку платежа.'
            else:
                text += '\n\nКлиент прислал подтверждение оплаты. Подтвердите бронь после проверки.'
        elif reservation.get('status') == 'cancelled':
            text += '\n\nЗаявка закрыта.'
        elif profile_from:
            text += '\n\nДействие выполнил: %s' % Misc.get_deeplink_with_name(profile_from)
        return text

    @classmethod
    def text_payment_proof_notice(cls, response, profile_from):
        reservation = response['reservation']
        offer = response['offer']
        text = (
            'Получено подтверждение оплаты по брони №%s\n'
            'Объявление: %s\n'
            'От: %s'
        ) % (
            reservation.get('sequence_number') or reservation.get('id'),
            html.quote(offer.get('title') or offer.get('item_text') or 'Прокат'),
            Misc.get_deeplink_with_name(profile_from),
        )
        if reservation.get('recipient_kind') == 'system':
            text += '\nПлатеж направлен системе; бронь держится под доверие.'
        return text

    @classmethod
    async def send_payment_proof_notice(cls, response, profile_from):
        recipients = []
        owner = response.get('owner') or {}
        if owner:
            recipients.append(owner)
        reservation = response.get('reservation') or {}
        payment_recipient = response.get('payment_recipient') or {}
        if reservation.get('recipient_kind') == 'system' and payment_recipient:
            recipients.append(payment_recipient)
        seen_tg_uids = set()
        for recipient in recipients:
            for tg_account in recipient.get('tg_data') or []:
                tg_uid = tg_account.get('tg_uid')
                if not tg_uid or tg_uid in seen_tg_uids:
                    continue
                seen_tg_uids.add(tg_uid)
                try:
                    await bot.send_message(
                        tg_uid,
                        text=cls.text_payment_proof_notice(response, profile_from),
                        reply_markup=cls.markup_reservation_owner(reservation)
                            if recipient == owner else None,
                    )
                except (TelegramBadRequest, TelegramForbiddenError):
                    pass

    @classmethod
    async def forward_payment_proof_pack(cls, response, uuid_pack):
        recipients = []
        owner = response.get('owner') or {}
        if owner:
            recipients.append(owner)
        reservation = response.get('reservation') or {}
        payment_recipient = response.get('payment_recipient') or {}
        if reservation.get('recipient_kind') == 'system' and payment_recipient:
            recipients.append(payment_recipient)
        sent_to = set()
        success = False
        for recipient in recipients:
            username = recipient.get('username')
            if not username or username in sent_to:
                continue
            sent_to.add(username)
            payload_send_pack = dict(
                tg_token=settings.TOKEN,
                uuid_pack=uuid_pack,
                username=username,
                what='tgdesc',
            )
            status_send_pack, response_send_pack = await Misc.api_request(
                path='/api/show_tgmsg_pack',
                method='post',
                json=payload_send_pack,
            )
            if status_send_pack == 200:
                success = True
        return success


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMRentalOffer.ask))
async def process_rental_offer(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if status_from != 200 or profile_from['uuid'] != data.get('user_uuid'):
        await state.clear()
        return
    if message.content_type == ContentType.LOCATION and message.location:
        await state.update_data(
            latitude=message.location.latitude,
            longitude=message.location.longitude,
        )
        await message.reply(
            'Локация сохранена. Теперь пришлите описание предмета, сроков и цены.',
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        return
    text = await Rental.message_or_voice_text(message, allow_voice_placeholder=True)
    if not text and message.content_type not in (
        ContentType.PHOTO,
        ContentType.VIDEO,
        ContentType.DOCUMENT,
        ContentType.AUDIO,
        ContentType.VOICE,
    ):
        await message.reply(Rental.PROMPT_OFFER, reply_markup=Misc.reply_markup_cancel_row())
        return
    slots = Rental.extract_slots(text)
    for key in ('latitude', 'longitude'):
        if slots.get(key) is None and data.get(key) is not None:
            slots[key] = data[key]
    payload = dict(
        user_uuid=profile_from['uuid'],
        visibility='authenticated',
        tgdesc=TgDesc.from_message(message, data['uuid_pack']),
    )
    payload.update({key: value for key, value in slots.items() if value not in (None, '')})
    key = f'{Rcache.RENTAL_DESC_PREFIX}{Rcache.KEY_SEP}{data["uuid_pack"]}'
    is_first = Misc.redis_is_key_first_up(key)
    if is_first is None:
        is_first = True
    if data.get('rental_offer_uuid'):
        payload.update(
            offer_uuid=data['rental_offer_uuid'],
            is_first=False,
        )
        status, response = await Rental.put_offer(payload)
    else:
        status, response = await Rental.create_offer(payload)
        if status == 200:
            await state.update_data(rental_offer_uuid=response['offer']['uuid'])
    if status != 200:
        await message.reply((response or {}).get('message') or 'Не удалось сохранить объявление')
        await state.clear()
        return
    await Rental.register_message(
        response['offer']['uuid'],
        'owner_offer',
        message.chat.id,
        message.message_id,
        recipient_uuid=profile_from['uuid'],
    )
    if not is_first:
        return
    if message.media_group_id:
        wait_last = await Misc.redis_wait_last_in_pack(key)
        if wait_last is False:
            return
    await state.clear()
    await message.reply('Объявление проката сохранено')
    await Rental.show_offer(message, profile_from, response['offer'])


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMRentalSearch.ask))
async def process_rental_search(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    query = await Rental.message_or_voice_text(message)
    if not query:
        await message.reply(
            'Голосовое распознавание сейчас недоступно. Пришлите запрос текстом.',
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        return
    await Rental.handle_search_text(message, state, query)


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.RENTAL_BOOK,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_rental_book(callback: CallbackQuery, state: FSMContext):
    try:
        offer_uuid = callback.data.split(KeyboardType.SEP)[1]
    except (IndexError, ValueError):
        await callback.answer()
        return
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await callback.answer()
        return
    status_reserve, response_reserve = await Rental.reserve(
        offer_uuid,
        profile_from,
        source_message=callback.message,
    )
    if status_reserve != 200:
        await callback.message.reply(
            (response_reserve or {}).get('message') or 'Не удалось создать заявку на бронь'
        )
        await callback.answer()
        return
    sent = await callback.message.reply(
        Rental.text_reservation(response_reserve),
        reply_markup=Rental.markup_reservation_consumer(response_reserve['reservation']),
    )
    await Rental.register_message(
        offer_uuid,
        'booking_prompt',
        sent.chat.id,
        sent.message_id,
        recipient_uuid=profile_from['uuid'],
    )
    owner = response_reserve.get('owner') or {}
    owner_notice = Rental.text_owner_reservation_notice(response_reserve, profile_from)
    delivered = 0
    for tg_account in owner.get('tg_data') or []:
        try:
            await bot.send_message(
                tg_account['tg_uid'],
                text=owner_notice,
                reply_markup=Rental.markup_reservation_owner(response_reserve['reservation']),
            )
            delivered += 1
        except (TelegramBadRequest, TelegramForbiddenError):
            pass
    if delivered == 0:
        await callback.message.reply('Заявка сохранена, но владельцу не удалось отправить уведомление в Telegram')
    await callback.answer()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.RENTAL_RESERVATION_ACTION,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_rental_reservation_action(callback: CallbackQuery, state: FSMContext):
    parts = (callback.data or '').split(KeyboardType.SEP)
    if len(parts) != 3:
        await callback.answer()
        return
    action = parts[1]
    reservation_id = parts[2]
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await callback.answer()
        return
    if action == Rental.ACTION_PAYMENT_REPORTED:
        await state.set_state(FSMRentalPaymentProof.ask)
        await state.update_data(
            user_uuid=profile_from['uuid'],
            reservation_id=reservation_id,
            uuid_pack=str(uuid4()),
        )
        await callback.message.reply(
            'Пришлите подтверждение оплаты: фото, скриншот, документ, видео, голосовое или текстовый комментарий.',
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        await callback.answer()
        return
    status_action, response_action = await Rental.reservation_action(
        reservation_id,
        profile_from,
        action,
    )
    if status_action != 200:
        await callback.message.reply(
            (response_action or {}).get('message') or 'Не удалось обновить заявку'
        )
        await callback.answer()
        return

    reservation = response_action['reservation']
    event = response_action.get('event') or {}
    owner = response_action.get('owner') or {}
    requester = response_action.get('requester') or {}
    actor_role = event.get('actor_role')

    if actor_role == 'requester':
        await callback.message.reply(
            Rental.text_consumer_reservation_update(response_action),
            reply_markup=Rental.markup_reservation_consumer(reservation),
        )
        owner_text = Rental.text_owner_reservation_update(response_action, profile_from)
        for tg_account in owner.get('tg_data') or []:
            try:
                await bot.send_message(
                    tg_account['tg_uid'],
                    text=owner_text,
                    reply_markup=Rental.markup_reservation_owner(reservation),
                )
            except (TelegramBadRequest, TelegramForbiddenError):
                pass
    elif actor_role == 'owner':
        await callback.message.reply(
            Rental.text_owner_reservation_update(response_action, profile_from),
            reply_markup=Rental.markup_reservation_owner(reservation),
        )
        consumer_text = Rental.text_consumer_reservation_update(response_action)
        for tg_account in requester.get('tg_data') or []:
            try:
                await bot.send_message(
                    tg_account['tg_uid'],
                    text=consumer_text,
                    reply_markup=Rental.markup_reservation_consumer(reservation),
                )
            except (TelegramBadRequest, TelegramForbiddenError):
                pass
    else:
        await callback.message.reply(Rental.text_reservation_status(response_action))
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMRentalPaymentProof.ask))
async def process_rental_payment_proof(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if status_from != 200 or profile_from['uuid'] != data.get('user_uuid'):
        await state.clear()
        return
    key = f'{Rcache.RENTAL_PAYMENT_PROOF_PREFIX}{Rcache.KEY_SEP}{data["uuid_pack"]}'
    if not await Misc.check_none_n_clear(is_first := Misc.redis_is_key_first_up(key), state):
        return
    status, response = await Rental.payment_proof(
        data['reservation_id'],
        profile_from,
        message,
        data['uuid_pack'],
    )
    if status != 200:
        await message.reply((response or {}).get('message') or 'Не удалось сохранить подтверждение')
        await state.clear()
        return
    if not is_first:
        return
    if message.media_group_id:
        wait_last = await Misc.redis_wait_last_in_pack(key)
        if not await Misc.check_none_n_clear(wait_last, state):
            return
    await Rental.send_payment_proof_notice(response, profile_from)
    forwarded = await Rental.forward_payment_proof_pack(response, data['uuid_pack'])
    await message.reply(
        Rental.text_consumer_reservation_update(response)
        if forwarded else
        Rental.text_consumer_reservation_update(response) + '\n\nПодтверждение сохранено, но переслать его получателю сейчас не удалось.',
        reply_markup=Rental.markup_reservation_consumer(response['reservation']),
    )
    await state.clear()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.RENTAL_CONTACT,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_rental_contact(callback: CallbackQuery, state: FSMContext):
    try:
        offer_uuid = callback.data.split(KeyboardType.SEP)[1]
    except (IndexError, ValueError):
        await callback.answer()
        return
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from == 200:
        await state.set_state(FSMRentalContact.ask)
        await state.update_data(
            user_uuid=profile_from['uuid'],
            offer_uuid=offer_uuid,
        )
        await callback.message.reply(
            'Напишите сообщение владельцу объявления.',
            reply_markup=Misc.reply_markup_cancel_row(),
        )
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMRentalContact.ask))
async def process_rental_contact(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if status_from != 200 or profile_from['uuid'] != data.get('user_uuid'):
        await state.clear()
        return
    text = Rental.message_text(message)
    if not text:
        await message.reply('Пришлите текст сообщения владельцу.', reply_markup=Misc.reply_markup_cancel_row())
        return
    status, response = await Rental.contact(data['offer_uuid'], profile_from, text)
    if status != 200:
        await message.reply((response or {}).get('message') or 'Не удалось передать сообщение')
        await state.clear()
        return
    owner = response.get('owner') or {}
    offer = response.get('offer') or {}
    delivered = 0
    msg_to_owner = (
        'Запрос по объявлению проката:\n'
        '%s\n\n'
        'От %s:\n%s'
    ) % (
        html.quote(offer.get('title') or offer.get('item_text') or 'Прокат'),
        Misc.get_deeplink_with_name(profile_from),
        html.quote(text),
    )
    for tg_account in owner.get('tg_data') or []:
        try:
            await bot.send_message(tg_account['tg_uid'], text=msg_to_owner)
            delivered += 1
        except (TelegramBadRequest, TelegramForbiddenError):
            pass
    await message.reply('Сообщение передано владельцу' if delivered else 'Запрос сохранен, но владельцу не удалось отправить сообщение в Telegram')
    await state.clear()
