# handler_rental.py
#
# Команды и сообщения для проката снаряжения.

import re
import datetime
from urllib.parse import urlencode
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
    ACTION_PAYMENT_PROOF_REJECTED = 'payment_proof_rejected'
    ACTION_CANCEL = 'cancel'
    ACTIONS_RESERVATION = {
        ACTION_OWNER_ACCEPT,
        ACTION_PAYMENT_REPORTED,
        ACTION_OWNER_CONFIRM,
        ACTION_PAYMENT_PROOF_REJECTED,
        ACTION_CANCEL,
    }
    ACTION_OWNER_LIST = 'list'
    ACTION_OWNER_ACTIVATE = 'activate'
    ACTION_OWNER_PAUSE = 'pause'
    ACTION_OWNER_ARCHIVE = 'archive'
    ACTIONS_OWNER = {
        ACTION_OWNER_LIST,
        ACTION_OWNER_ACTIVATE,
        ACTION_OWNER_PAUSE,
        ACTION_OWNER_ARCHIVE,
    }
    OWNER_ACTION_STATUS = {
        ACTION_OWNER_ACTIVATE: 'active',
        ACTION_OWNER_PAUSE: 'paused',
        ACTION_OWNER_ARCHIVE: 'archived',
    }
    OWNER_LIST_STATUSES = {'all', 'active', 'paused', 'archived'}

    MSG_CALLBACK_STALE = 'Эта кнопка устарела. Откройте прокат заново через /rent_search или /rent.'
    MSG_CALLBACK_AUTH = 'Не удалось проверить ваш профиль. Откройте бота командой /start и попробуйте еще раз.'

    OFFER_STATUS_LABELS = {
        'draft': 'черновик',
        'active': 'активно',
        'paused': 'на паузе',
        'archived': 'архив',
    }

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
    EVENT_LABELS = {
        'created': 'создана',
        'owner_accept': 'принята владельцем',
        'payment_reported': 'оплата отмечена',
        'payment_proof_submitted': 'подтверждение оплаты отправлено',
        'payment_proof_rejected': 'подтверждение оплаты отклонено',
        'owner_confirm': 'подтверждена владельцем',
        'cancel': 'отменена',
        'expire': 'истекла',
    }

    @classmethod
    def message_text(cls, message):
        return (message.text or message.caption or '').strip()

    @classmethod
    def get_deeplink(cls, offer_uuid):
        return Misc.get_start_deeplink(f'rent-{offer_uuid}', https=True)

    @classmethod
    def get_map_url(cls, offer):
        if offer.get('latitude') is None or offer.get('longitude') is None:
            return ''
        params = dict(
            rental='on',
            rental_uuid=offer['uuid'],
        )
        title = offer.get('title') or offer.get('item_text') or ''
        if title:
            params.update(rental_query=title)
        return '%s/?%s' % (settings.MAP_HOST.rstrip('/'), urlencode(params))

    @classmethod
    def stt_headers(cls):
        headers = {}
        if getattr(settings, 'RENTAL_STT_TOKEN', ''):
            headers['Authorization'] = 'Bearer %s' % settings.RENTAL_STT_TOKEN
        return headers

    @classmethod
    async def stt_request_kwargs(cls, message):
        mode = getattr(settings, 'RENTAL_STT_MODE', 'file_id')
        contract = getattr(settings, 'RENTAL_STT_CONTRACT', 'organizm_hermes_v1')
        if mode == 'download':
            form = aiohttp.FormData()
            form.add_field('contract', contract)
            form.add_field('file_id', message.voice.file_id)
            form.add_field('telegram_user_id', str(message.from_user.id))
            form.add_field('language', getattr(settings, 'RENTAL_STT_LANGUAGE', 'ru'))
            form.add_field(
                'voice',
                await Misc.get_file_bytes(message.voice),
                filename='voice.ogg',
                content_type=message.voice.mime_type or 'audio/ogg',
            )
            return dict(data=form)
        return dict(json=dict(
            contract=contract,
            source='telegram_voice',
            file_id=message.voice.file_id,
            duration=message.voice.duration,
            mime_type=message.voice.mime_type or '',
            telegram_user_id=message.from_user.id,
            language=getattr(settings, 'RENTAL_STT_LANGUAGE', 'ru'),
        ))

    @classmethod
    def stt_transcript_from_response(cls, data):
        if isinstance(data, str):
            return data.strip()
        if not isinstance(data, dict):
            return ''
        result = data.get('transcript') or data.get('text') or ''
        for key in ('result', 'data'):
            if result:
                break
            nested = data.get(key)
            if isinstance(nested, dict):
                result = nested.get('transcript') or nested.get('text') or ''
        return str(result).strip()

    @classmethod
    async def voice_transcript(cls, message):
        url = getattr(settings, 'RENTAL_STT_URL', '')
        if not url or not message.voice:
            return ''
        timeout = aiohttp.ClientTimeout(total=getattr(settings, 'HTTP_TIMEOUT', 60))
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                request_kwargs = await cls.stt_request_kwargs(message)
                async with session.post(url, headers=cls.stt_headers(), **request_kwargs) as resp:
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
        return cls.stt_transcript_from_response(data)

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
            '/rent_search - найти снаряжение\n'
            '/rent_my - мои объявления\n'
            '/rent_history - мои брони'
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
    async def cmd_rent_my(cls, message: Message, state: FSMContext):
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        await cls.send_owner_offers(message, response_sender)

    @classmethod
    async def cmd_rent_history(cls, message: Message, state: FSMContext):
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        await cls.send_reservation_history(message, response_sender)

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
    async def list_owner_offers(cls, profile_from, status_filter='all'):
        params = dict(
            tg_token=settings.TOKEN,
            owner_uuid=profile_from['uuid'],
            number=20,
        )
        if status_filter and status_filter != 'all':
            params.update(status=status_filter)
        status, response = await Misc.api_request(
            path='/api/rental/offer',
            method='get',
            params=params,
        )
        return status, response

    @classmethod
    async def list_reservations(cls, profile_from, role='all', status_group='open'):
        params = dict(
            tg_token=settings.TOKEN,
            user_uuid=profile_from['uuid'],
            role=role,
            status_group=status_group,
            number=10,
        )
        status, response = await Misc.api_request(
            path='/api/rental/reservation',
            method='get',
            params=params,
        )
        return status, response

    @classmethod
    async def set_owner_offer_status(cls, offer_uuid, profile_from, status_value):
        return await cls.put_offer(dict(
            user_uuid=profile_from['uuid'],
            offer_uuid=offer_uuid,
            status=status_value,
        ))

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
            *([[
                InlineKeyboardButton(
                    text='На карте',
                    url=cls.get_map_url(offer),
                )
            ]] if cls.get_map_url(offer) else []),
        ])

    @classmethod
    def offer_status_label(cls, offer):
        return cls.OFFER_STATUS_LABELS.get(
            offer.get('status'),
            offer.get('status') or 'статус неизвестен',
        )

    @classmethod
    def owner_action_callback_data(cls, action, value):
        return '%s%s%s%s%s' % (
            KeyboardType.RENTAL_OWNER_ACTION,
            KeyboardType.SEP,
            action,
            KeyboardType.SEP,
            value,
        )

    @classmethod
    def parse_owner_action_callback_data(cls, callback):
        parts = (callback.data or '').split(KeyboardType.SEP)
        if (
            len(parts) != 3 or
            parts[0] != str(KeyboardType.RENTAL_OWNER_ACTION) or
            parts[1] not in cls.ACTIONS_OWNER
        ):
            return '', ''
        action, value = parts[1], parts[2]
        if action == cls.ACTION_OWNER_LIST:
            if value not in cls.OWNER_LIST_STATUSES:
                return '', ''
        elif not value:
            return '', ''
        return action, value

    @classmethod
    def text_owner_offer(cls, offer):
        result = '<b>%s</b>\n' % html.quote(offer.get('title') or offer.get('item_text') or 'Прокат')
        result += 'Статус: %s\n' % html.quote(cls.offer_status_label(offer))
        if offer.get('price_text'):
            result += 'Цена: %s\n' % html.quote(offer['price_text'])
        elif offer.get('price_amount'):
            result += 'Цена: %s %s %s\n' % (
                html.quote(offer.get('price_amount') or ''),
                html.quote(offer.get('price_currency') or ''),
                html.quote(offer.get('price_period') or ''),
            )
        if offer.get('availability_text') or offer.get('available_from') or offer.get('available_to'):
            availability = offer.get('availability_text') or ''
            if offer.get('available_from') or offer.get('available_to'):
                availability += ' %s - %s' % (offer.get('available_from') or '?', offer.get('available_to') or '?')
            result += 'Доступность: %s\n' % html.quote(availability.strip())
        if offer.get('address'):
            result += 'Адрес: %s\n' % html.quote(offer['address'])
        result += '\n%s' % Misc.get_html_a(cls.get_deeplink(offer['uuid']), 'Ссылка на объявление')
        return result

    @classmethod
    def markup_owner_offer(cls, offer):
        status = offer.get('status')
        rows = []
        if status == 'active':
            rows.append([
                InlineKeyboardButton(
                    text='Пауза',
                    callback_data=cls.owner_action_callback_data(
                        cls.ACTION_OWNER_PAUSE,
                        offer['uuid'],
                    ),
                )
            ])
        elif status in ('paused', 'archived', 'draft'):
            rows.append([
                InlineKeyboardButton(
                    text='Возобновить',
                    callback_data=cls.owner_action_callback_data(
                        cls.ACTION_OWNER_ACTIVATE,
                        offer['uuid'],
                    ),
                )
            ])
        if status != 'archived':
            rows.append([
                InlineKeyboardButton(
                    text='В архив',
                    callback_data=cls.owner_action_callback_data(
                        cls.ACTION_OWNER_ARCHIVE,
                        offer['uuid'],
                    ),
                )
            ])
        rows.append([
            InlineKeyboardButton(
                text='Открыть',
                url=cls.get_deeplink(offer['uuid']),
            )
        ])
        if cls.get_map_url(offer):
            rows.append([
                InlineKeyboardButton(
                    text='На карте',
                    url=cls.get_map_url(offer),
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @classmethod
    async def send_owner_offers(cls, message, profile_from, status_filter='all'):
        status, response = await cls.list_owner_offers(profile_from, status_filter=status_filter)
        if status != 200:
            await message.reply((response or {}).get('message') or 'Не удалось получить объявления')
            return
        offers = (response or {}).get('offers') or []
        if not offers:
            await message.reply('У вас пока нет объявлений проката')
            return
        for offer in offers:
            await message.reply(
                cls.text_owner_offer(offer),
                reply_markup=cls.markup_owner_offer(offer),
            )

    @classmethod
    def reservation_history_markup(cls, response):
        reservation = response.get('reservation') or {}
        if response.get('viewer_role') == 'owner':
            return cls.markup_reservation_owner(reservation)
        return cls.markup_reservation_consumer(reservation)

    @classmethod
    def text_reservation_audit(cls, response):
        events = response.get('events') or []
        proofs = response.get('payment_proofs') or []
        lines = []
        if events:
            shown_events = events[-4:]
            parts = []
            if len(events) > len(shown_events):
                parts.append('еще %s ранее' % (len(events) - len(shown_events)))
            for event in shown_events:
                event_text = cls.EVENT_LABELS.get(
                    event.get('event_type'),
                    event.get('event_type') or 'событие',
                )
                status_text = cls.STATUS_LABELS.get(event.get('status_to') or '')
                parts.append(
                    '%s -> %s' % (event_text, status_text)
                    if status_text else event_text
                )
            lines.append('События: %s' % '; '.join(parts))
        if proofs:
            proof_parts = []
            for proof in proofs[-2:]:
                label = (proof.get('uuid_pack') or str(proof.get('id') or ''))[:8]
                file_types = sorted({
                    message.get('file_type') or 'message'
                    for message in proof.get('messages') or []
                })
                if file_types:
                    label = '%s (%s)' % (label, ', '.join(file_types))
                proof_parts.append(label)
            lines.append('Подтверждения: %s' % ', '.join(proof_parts))
        return '\n'.join(lines)

    @classmethod
    def text_reservation_history_card(cls, response):
        text = cls.text_reservation_status(response)
        reservation = response.get('reservation') or {}
        role = response.get('viewer_role') or ''
        if role == 'owner':
            requester = response.get('requester') or {}
            text += '\nРоль: владелец'
            if requester:
                text += '\nОт: %s' % Misc.get_deeplink_with_name(requester)
        elif role == 'requester':
            owner = response.get('owner') or {}
            text += '\nРоль: арендатор'
            if owner:
                text += '\nВладелец: %s' % Misc.get_deeplink_with_name(owner)
        if reservation.get('date_from') or reservation.get('date_to'):
            text += '\nДаты: %s - %s' % (
                html.quote(reservation.get('date_from') or '?'),
                html.quote(reservation.get('date_to') or '?'),
            )
        audit = cls.text_reservation_audit(response)
        if audit:
            text += '\n\n%s' % audit
        return text

    @classmethod
    async def send_reservation_history_group(cls, message, title, reservations):
        if not reservations:
            return
        await message.reply(title)
        for response in reservations:
            await message.reply(
                cls.text_reservation_history_card(response),
                reply_markup=cls.reservation_history_markup(response),
            )

    @classmethod
    async def send_reservation_history(cls, message, profile_from):
        status_open, response_open = await cls.list_reservations(
            profile_from,
            status_group='open',
        )
        if status_open != 200:
            await message.reply((response_open or {}).get('message') or 'Не удалось получить брони')
            return
        status_closed, response_closed = await cls.list_reservations(
            profile_from,
            status_group='recent_closed',
        )
        if status_closed != 200:
            await message.reply((response_closed or {}).get('message') or 'Не удалось получить историю брони')
            return
        open_reservations = (response_open or {}).get('reservations') or []
        closed_reservations = (response_closed or {}).get('reservations') or []
        if not open_reservations and not closed_reservations:
            await message.reply('У вас пока нет броней проката')
            return
        await cls.send_reservation_history_group(
            message,
            'Активные брони',
            open_reservations,
        )
        await cls.send_reservation_history_group(
            message,
            'Недавно закрытые брони',
            closed_reservations,
        )

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
    def parse_offer_callback_data(cls, callback, keyboard_type):
        parts = (callback.data or '').split(KeyboardType.SEP)
        if len(parts) != 2 or parts[0] != str(keyboard_type) or not parts[1]:
            return ''
        return parts[1]

    @classmethod
    def parse_reservation_action_callback_data(cls, callback):
        parts = (callback.data or '').split(KeyboardType.SEP)
        if (
            len(parts) != 3 or
            parts[0] != str(KeyboardType.RENTAL_RESERVATION_ACTION) or
            parts[1] not in cls.ACTIONS_RESERVATION or
            not parts[2].isdigit()
        ):
            return '', ''
        return parts[1], parts[2]

    @classmethod
    async def answer_callback_notice(cls, callback, text):
        await callback.answer(text, show_alert=True)

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
        if status in ('sent', 'awaiting_payment'):
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
        if status == 'payment_proof_submitted':
            rows.append([
                InlineKeyboardButton(
                    text='Отклонить чек',
                    callback_data=cls.reservation_action_callback_data(
                        cls.ACTION_PAYMENT_PROOF_REJECTED,
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
        hold_seconds = reservation.get('hold_seconds') or reservation.get('hold_seconds_remaining') or 0
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
        event = response.get('event') or {}
        if reservation.get('status') == 'owner_accepted':
            text += '\n\nВладелец принял заявку. Если условия подходят, сообщите об оплате кнопкой ниже.'
        elif reservation.get('status') == 'payment_proof_submitted':
            if reservation.get('recipient_kind') == 'system':
                text += '\n\nПодтверждение получено; бронь держится под доверие. Не называйте это проверенной оплатой до аудита.'
            else:
                text += '\n\nПодтверждение получено и передано владельцу.'
        elif reservation.get('status') == 'confirmed':
            text += '\n\nВладелец подтвердил бронь.'
        elif event.get('event_type') == 'payment_proof_rejected':
            text += (
                '\n\nВладелец отклонил подтверждение оплаты. Бронь закрыта, даты освобождены. '
                'Доверие и недоверие не меняются автоматически; профильные действия остаются отдельными.'
            )
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
        elif (response.get('event') or {}).get('event_type') == 'payment_proof_rejected':
            text += (
                '\n\nПодтверждение оплаты отклонено. Бронь закрыта, даты освобождены. '
                'Доверие/недоверие в профиле нужно менять отдельным действием, если это требуется.'
            )
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
    offer_uuid = Rental.parse_offer_callback_data(callback, KeyboardType.RENTAL_BOOK)
    if not offer_uuid:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
        return
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_AUTH)
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
    action, reservation_id = Rental.parse_reservation_action_callback_data(callback)
    if not action:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
        return
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_AUTH)
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


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.RENTAL_OWNER_ACTION,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_rental_owner_action(callback: CallbackQuery, state: FSMContext):
    action, value = Rental.parse_owner_action_callback_data(callback)
    if not action:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
        return
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_AUTH)
        return
    if action == Rental.ACTION_OWNER_LIST:
        await Rental.send_owner_offers(callback.message, profile_from, status_filter=value)
        await callback.answer()
        return
    status_value = Rental.OWNER_ACTION_STATUS[action]
    status_action, response_action = await Rental.set_owner_offer_status(
        value,
        profile_from,
        status_value,
    )
    if status_action != 200:
        await callback.message.reply(
            (response_action or {}).get('message') or 'Не удалось обновить объявление'
        )
        await callback.answer()
        return
    offer = response_action['offer']
    await callback.message.reply(
        Rental.text_owner_offer(offer),
        reply_markup=Rental.markup_owner_offer(offer),
    )
    await callback.answer('Статус обновлен')


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
    offer_uuid = Rental.parse_offer_callback_data(callback, KeyboardType.RENTAL_CONTACT)
    if not offer_uuid:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
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
    else:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_AUTH)


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
