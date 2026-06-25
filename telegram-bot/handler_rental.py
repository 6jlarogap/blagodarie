# handler_rental.py
#
# Команды и сообщения для проката снаряжения.

import re
import datetime
import json
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


class FSMRentalIntro(StatesGroup):
    ask = State()


class FSMRentalContact(StatesGroup):
    ask = State()


class FSMRentalPaymentProof(StatesGroup):
    ask = State()


class Rental(object):

    PROMPT_OFFER = (
        'Опишите одним сообщением: что сдаёте, где забрать, когда доступно, '
        'цена/залог/условия. Потом я покажу черновик, вы подтвердите или поправите, '
        'и после сохранения можно будет добавить фото/видео.'
    )
    PROMPT_OFFER_WITH_VOICE = (
        'Расскажите одним голосовым или текстом: что сдаёте, где забрать, когда доступно, '
        'цена/залог/условия. Потом я покажу черновик, вы подтвердите или поправите, '
        'и после сохранения можно будет добавить фото/видео.'
    )
    PROMPT_RENT_INTRO = (
        'Прокат: напишите или скажите голосом одним сообщением.\n\n'
        'Сдать: «сдам палатку на ВДНХ с 1 по 3 июля за 500 руб/день».\n'
        'Найти: «ищу палатку на выходные возле ВДНХ».'
    )
    OFFER_MISSING_LABELS = {
        'item': 'что сдаете',
        'place': 'где забрать или координаты',
        'availability': 'когда доступно',
        'price': 'цена или условия оплаты',
    }
    PROMPT_SEARCH = 'Что ищем в прокат? Укажите предмет, место или даты одним сообщением.'
    PROMPT_SEARCH_CONTEXT = 'Где или на какие даты искать?'
    PROMPT_SEARCH_CONTEXT_WITH_VOICE = 'Где или на какие даты искать? Можно ответить голосом.'

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
    ACTION_GEOCODE_USE = 'use'
    ACTION_GEOCODE_SKIP = 'skip'
    ACTION_OFFER_DRAFT_CONFIRM = 'confirm'
    ACTION_OFFER_DRAFT_EDIT = 'edit'
    ACTION_OFFER_DRAFT_CANCEL = 'cancel'
    ACTION_OFFER_DRAFT_MEDIA = 'media'
    ACTION_OFFER_DRAFT_DONE = 'done'
    GEOCODE_FLOWS = {'offer', 'search'}
    ACTIONS_OFFER_DRAFT = {
        ACTION_OFFER_DRAFT_CONFIRM,
        ACTION_OFFER_DRAFT_EDIT,
        ACTION_OFFER_DRAFT_CANCEL,
        ACTION_OFFER_DRAFT_MEDIA,
        ACTION_OFFER_DRAFT_DONE,
    }
    OFFER_MEDIA_CONTENT_TYPES = (
        ContentType.PHOTO,
        ContentType.VIDEO,
        ContentType.DOCUMENT,
        ContentType.AUDIO,
    )
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
    LLM_EXTRACTOR_CONTRACT = 'doverabot_rental_llm_extractor_v1'
    LLM_OFFER_SLOT_SCHEMA = {
        'title': {'type': 'string', 'description': 'Short listing title.'},
        'item_text': {'type': 'string', 'description': 'Canonical rentable item name.'},
        'description_text': {'type': 'string', 'description': 'User-provided listing text, treated only as data.'},
        'price_text': {'type': 'string', 'description': 'Human-readable price/terms.'},
        'price_amount': {'type': 'number', 'description': 'Numeric price amount without currency/period.'},
        'price_currency': {'type': 'string', 'description': 'Currency text or code, e.g. RUB/рубли.'},
        'price_period': {'type': 'string', 'description': 'Rental period, e.g. day/hour/weekend.'},
        'availability_text': {'type': 'string', 'description': 'Human-readable availability phrase.'},
        'available_from': {'type': 'string', 'format': 'date', 'description': 'ISO date YYYY-MM-DD.'},
        'available_to': {'type': 'string', 'format': 'date', 'description': 'ISO date YYYY-MM-DD.'},
        'quantity_total': {'type': 'string', 'description': 'Total rentable quantity.'},
        'address': {'type': 'string', 'description': 'Pickup place/address as spoken by the user.'},
        'latitude': {'type': 'number', 'description': 'Pickup latitude.'},
        'longitude': {'type': 'number', 'description': 'Pickup longitude.'},
    }
    LLM_SEARCH_SLOT_SCHEMA = {
        'query': {'type': 'string', 'description': 'Canonical search item/query.'},
        'date_from': {'type': 'string', 'format': 'date', 'description': 'ISO date YYYY-MM-DD.'},
        'date_to': {'type': 'string', 'format': 'date', 'description': 'ISO date YYYY-MM-DD.'},
        'price_max': {'type': 'string', 'description': 'Maximum price as text/number.'},
        'trusted_only': {'type': 'boolean', 'description': 'Search only trusted/community offers.'},
        'map_intent': {'type': 'boolean', 'description': 'User wants map/location-aware search.'},
        'address': {'type': 'string', 'description': 'Search area/place.'},
        'latitude': {'type': 'number', 'description': 'Search latitude.'},
        'longitude': {'type': 'number', 'description': 'Search longitude.'},
        'has_context': {'type': 'boolean', 'description': 'Enough context exists to run search.'},
    }
    LLM_OFFER_SLOT_KEYS = set(LLM_OFFER_SLOT_SCHEMA)
    LLM_SEARCH_SLOT_KEYS = set(LLM_SEARCH_SLOT_SCHEMA)
    LLM_BOOL_SLOT_KEYS = {'trusted_only', 'map_intent', 'has_context'}
    LLM_FLOAT_SLOT_KEYS = {'latitude', 'longitude', 'price_amount'}
    LLM_DATE_SLOT_KEYS = {'available_from', 'available_to', 'date_from', 'date_to'}
    SECRET_LOG_KEY_MARKERS = {'authorization', 'api_key', 'token', 'secret', 'password'}

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
    def offer_prompt(cls):
        if getattr(settings, 'RENTAL_STT_URL', ''):
            return cls.PROMPT_OFFER_WITH_VOICE
        return cls.PROMPT_OFFER

    @classmethod
    def search_context_prompt(cls):
        if getattr(settings, 'RENTAL_STT_URL', ''):
            return cls.PROMPT_SEARCH_CONTEXT_WITH_VOICE
        return cls.PROMPT_SEARCH_CONTEXT

    @classmethod
    def command_args(cls, message, command):
        text = cls.message_text(message)
        return re.sub(
            r'^\s*/%s(?:@\w+)?(?:\s+|$)' % re.escape(command),
            '',
            text,
            count=1,
            flags=re.IGNORECASE,
        ).strip()

    @classmethod
    def classify_rent_intro(cls, text):
        text = (text or '').strip().lower()
        if not text:
            return ''
        offer_pattern = (
            r'\b(сдам|сдаю|сдать|сдаётся|сдается|предлагаю|отдам|дам)\b|'
            r'\b(у меня|есть)\b.*\b(прокат|аренд|сдам|сдаю|можно взять)\b|'
            r'^есть\s+\S+'
        )
        search_pattern = (
            r'\b(ищу|нужн[аоы]?|хочу взять|возьму|найди|найти|поиск|арендую|нужен)\b'
        )
        has_offer = bool(re.search(offer_pattern, text))
        has_search = bool(re.search(search_pattern, text))
        if has_offer and not has_search:
            return 'offer'
        if has_search and not has_offer:
            return 'search'
        return ''

    @classmethod
    def debug_log_enabled(cls):
        return bool(getattr(settings, 'RENTAL_DEBUG_LOG_CONVERSATION', False))

    @classmethod
    def debug_log_value(cls, value, key=''):
        lower_key = str(key or '').lower()
        if any(marker in lower_key for marker in cls.SECRET_LOG_KEY_MARKERS):
            return '[redacted]'
        limit = getattr(settings, 'RENTAL_DEBUG_LOG_TEXT_LIMIT', 1200)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 1200
        if isinstance(value, dict):
            return {
                str(item_key): cls.debug_log_value(item, key=item_key)
                for item_key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [
                cls.debug_log_value(item, key=key)
                for item in value
            ]
        if isinstance(value, str) and limit > 0 and len(value) > limit:
            return value[:limit] + '...'
        return value

    @classmethod
    def log_debug(cls, event, message=None, **fields):
        if not cls.debug_log_enabled():
            return
        payload = dict(event=event)
        if message:
            from_user = getattr(message, 'from_user', None)
            chat = getattr(message, 'chat', None)
            payload.update(
                chat_id=getattr(chat, 'id', None),
                message_id=getattr(message, 'message_id', None),
                user_id=getattr(from_user, 'id', None),
                username=getattr(from_user, 'username', ''),
                content_type=getattr(message, 'content_type', ''),
            )
        for key, value in fields.items():
            payload[key] = cls.debug_log_value(value, key=key)
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        logging.info('rental_debug %s', payload_json)
        print('rental_debug %s' % payload_json, flush=True)

    @classmethod
    def llm_extractor_headers(cls):
        headers = {}
        if getattr(settings, 'RENTAL_LLM_EXTRACTOR_TOKEN', ''):
            headers['Authorization'] = 'Bearer %s' % settings.RENTAL_LLM_EXTRACTOR_TOKEN
        return headers

    @classmethod
    def llm_extractor_timeout(cls):
        try:
            timeout = float(getattr(settings, 'RENTAL_LLM_EXTRACTOR_TIMEOUT', 30))
        except (TypeError, ValueError):
            timeout = 30
        return timeout if timeout > 0 else 30

    @classmethod
    def llm_slot_keys(cls, mode):
        return cls.LLM_SEARCH_SLOT_KEYS if mode == 'search' else cls.LLM_OFFER_SLOT_KEYS

    @classmethod
    def llm_slot_schema(cls, mode):
        schema = cls.LLM_SEARCH_SLOT_SCHEMA if mode == 'search' else cls.LLM_OFFER_SLOT_SCHEMA
        return {key: dict(value) for key, value in schema.items()}

    @classmethod
    def llm_response_schema(cls, mode):
        return {
            'slots': {
                'type': 'object',
                'additionalProperties': False,
                'properties': cls.llm_slot_schema(mode),
            },
        }

    @classmethod
    def llm_current_slots(cls, mode, slots):
        allowed = cls.llm_slot_keys(mode)
        return {
            key: value
            for key, value in (slots or {}).items()
            if key in allowed and value not in (None, '')
        }

    @classmethod
    def llm_extractor_payload(cls, mode, text, current_slots=None):
        contract = getattr(settings, 'RENTAL_LLM_EXTRACTOR_CONTRACT', cls.LLM_EXTRACTOR_CONTRACT)
        language = getattr(settings, 'RENTAL_STT_LANGUAGE', 'ru')
        model = getattr(settings, 'RENTAL_LLM_EXTRACTOR_MODEL', '')
        current_slots = cls.llm_current_slots(mode, current_slots)
        payload = dict(
            contract=contract,
            mode=mode,
            text=text,
            language=language,
            model=model,
            metadata=dict(
                language=language,
                model=model,
                contract=contract,
            ),
            current_slots=current_slots,
            slots=current_slots or {},
            schema=cls.llm_slot_schema(mode),
            response_schema=cls.llm_response_schema(mode),
        )
        return payload

    @classmethod
    def normalize_llm_text_slot(cls, value):
        if value in (None, '') or isinstance(value, (dict, list, tuple)):
            return ''
        return str(value).strip()

    @classmethod
    def normalize_llm_bool_slot(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {'true', '1', 'yes', 'on', 'да'}:
                return True
            if normalized in {'false', '0', 'no', 'off', 'нет'}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return False

    @classmethod
    def normalize_llm_float_slot(cls, value):
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def llm_slots_from_response(cls, data, mode):
        if not isinstance(data, dict):
            return {}
        candidate = data
        for key in ('slots', mode, 'extraction', 'result', 'data'):
            nested = data.get(key)
            if not isinstance(nested, dict):
                continue
            if isinstance(nested.get('slots'), dict):
                candidate = nested['slots']
                break
            candidate = nested
            break
        if not isinstance(candidate, dict):
            return {}
        result = {}
        for key in cls.llm_slot_keys(mode):
            if key not in candidate:
                continue
            value = candidate[key]
            if key in cls.LLM_BOOL_SLOT_KEYS:
                result[key] = cls.normalize_llm_bool_slot(value)
                continue
            if key in cls.LLM_FLOAT_SLOT_KEYS:
                normalized_float = cls.normalize_llm_float_slot(value)
                if normalized_float is not None:
                    result[key] = normalized_float
                continue
            if key in cls.LLM_DATE_SLOT_KEYS:
                normalized_date = cls.parse_search_date(str(value))
                if normalized_date:
                    result[key] = normalized_date
                continue
            normalized_text = cls.normalize_llm_text_slot(value)
            if normalized_text:
                result[key] = normalized_text
        return result

    @classmethod
    def merge_llm_slots(cls, base_slots, llm_slots, mode, raw_text=''):
        merged = dict(base_slots or {})
        raw_text = (raw_text or '').strip()
        allowed = cls.llm_slot_keys(mode)
        correction_hint = bool(re.search(r'\bне\s+.+?\bа\s+', raw_text, flags=re.I))
        refine_text_keys = {'title', 'item_text', 'query'}
        for key, value in (llm_slots or {}).items():
            if key not in allowed:
                continue
            current = merged.get(key)
            if key in cls.LLM_BOOL_SLOT_KEYS:
                if value and not current:
                    merged[key] = True
                continue
            if key in cls.LLM_FLOAT_SLOT_KEYS:
                if current in (None, ''):
                    merged[key] = value
                continue
            if key in refine_text_keys:
                current_text = str(current or '').strip()
                if not current_text or current_text == raw_text or len(current_text) > 80:
                    merged[key] = value
                continue
            if key == 'description_text':
                if not current:
                    merged[key] = value
                continue
            if correction_hint and key in {'address', 'availability_text', 'price_text'}:
                merged[key] = value
                continue
            if current in (None, ''):
                merged[key] = value
        if mode == 'search':
            merged['has_context'] = bool(
                merged.get('has_context') or
                merged.get('date_from') or
                merged.get('date_to') or
                merged.get('price_max') or
                merged.get('trusted_only') or
                merged.get('address') or
                merged.get('latitude') is not None
            )
        return merged

    @classmethod
    async def llm_extract_slots(cls, mode, text, current_slots=None, message=None):
        url = getattr(settings, 'RENTAL_LLM_EXTRACTOR_URL', '')
        text = (text or '').strip()
        if not url or not text:
            return {}
        payload = cls.llm_extractor_payload(mode, text, current_slots=current_slots)
        timeout = aiohttp.ClientTimeout(total=cls.llm_extractor_timeout())
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=cls.llm_extractor_headers(), json=payload) as resp:
                    if resp.status >= 400:
                        error_text = await resp.text()
                        logging.warning('rental LLM extractor failed with status %s', resp.status)
                        cls.log_debug(
                            'llm_extractor_failed',
                            message,
                            mode=mode,
                            status=resp.status,
                            response=error_text,
                        )
                        return {}
                    data = await resp.json(content_type=None)
        except Exception:
            logging.exception('rental LLM extractor request failed')
            cls.log_debug('llm_extractor_exception', message, mode=mode)
            return {}
        slots = cls.llm_slots_from_response(data, mode)
        cls.log_debug(
            'llm_extractor_response',
            message,
            mode=mode,
            slots=slots,
            response=data,
        )
        return slots

    @classmethod
    async def extract_offer_slots(cls, text, message=None, current_slots=None):
        base_slots = cls.extract_slots(text)
        llm_slots = await cls.llm_extract_slots(
            'offer',
            text,
            current_slots=cls.merge_offer_slots(current_slots or {}, base_slots),
            message=message,
        )
        return cls.merge_llm_slots(base_slots, llm_slots, 'offer', raw_text=text)

    @classmethod
    async def extract_search_slots_with_llm(cls, text, message=None, current_slots=None):
        base_slots = cls.extract_search_slots(text)
        llm_slots = await cls.llm_extract_slots(
            'search',
            text,
            current_slots=current_slots or base_slots,
            message=message,
        )
        return cls.merge_llm_slots(base_slots, llm_slots, 'search', raw_text=text)

    @classmethod
    def get_deeplink(cls, offer_uuid):
        return Misc.get_start_deeplink(f'rent-{offer_uuid}', https=True)

    @classmethod
    def get_map_url(cls, offer, map_params=None):
        if offer.get('latitude') is None or offer.get('longitude') is None:
            return ''
        map_params = map_params or {}
        params = dict(
            rental='on',
            rental_uuid=offer['uuid'],
        )
        query = map_params.get('query') or offer.get('title') or offer.get('item_text') or ''
        if query:
            params.update(rental_query=query)
        equipment_types = offer.get('equipment_types') or []
        if equipment_types:
            equipment_slug = equipment_types[0].get('slug')
            if equipment_slug:
                params.update(rental_equipment_type=equipment_slug)
        date_from = map_params.get('date_from') or offer.get('available_from') or ''
        date_to = map_params.get('date_to') or offer.get('available_to') or ''
        if date_from:
            params.update(rental_date_from=date_from)
        if date_to:
            params.update(rental_date_to=date_to)
        price_max = map_params.get('price_max') or offer.get('price_amount') or ''
        if price_max:
            params.update(rental_price_max=price_max)
        if map_params.get('trusted_only'):
            params.update(rental_trusted_only='on')
        return '%s/rent/?%s' % (settings.MAP_HOST.rstrip('/'), urlencode(params))

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
    def stt_timeout(cls):
        try:
            timeout = float(getattr(settings, 'RENTAL_STT_TIMEOUT', 300))
        except (TypeError, ValueError):
            timeout = 300
        return timeout if timeout > 0 else 300

    @classmethod
    async def voice_transcript(cls, message):
        url = getattr(settings, 'RENTAL_STT_URL', '')
        if not url or not message.voice:
            cls.log_debug(
                'stt_skipped',
                message,
                reason='missing_stt_url' if not url else 'missing_voice',
            )
            return ''
        timeout = aiohttp.ClientTimeout(total=cls.stt_timeout())
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                request_kwargs = await cls.stt_request_kwargs(message)
                async with session.post(url, headers=cls.stt_headers(), **request_kwargs) as resp:
                    if resp.status >= 400:
                        error_text = await resp.text()
                        logging.warning('rental STT failed with status %s', resp.status)
                        cls.log_debug(
                            'stt_failed',
                            message,
                            status=resp.status,
                            response=error_text,
                        )
                        return ''
                    try:
                        data = await resp.json(content_type=None)
                    except (ValueError, aiohttp.ContentTypeError):
                        transcript = (await resp.text()).strip()
                        cls.log_debug(
                            'stt_response',
                            message,
                            status=resp.status,
                            transcript=transcript,
                            transcript_len=len(transcript),
                        )
                        return transcript
        except Exception:
            logging.exception('rental STT request failed')
            cls.log_debug('stt_exception', message)
            return ''
        transcript = cls.stt_transcript_from_response(data)
        cls.log_debug(
            'stt_response',
            message,
            status=resp.status,
            transcript=transcript,
            transcript_len=len(transcript),
            response=data,
        )
        return transcript

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
    def geocoding_headers(cls):
        headers = {}
        if getattr(settings, 'RENTAL_GEOCODING_TOKEN', ''):
            headers['Authorization'] = 'Bearer %s' % settings.RENTAL_GEOCODING_TOKEN
        return headers

    @classmethod
    async def geocode_provider_request(cls, address):
        url = getattr(settings, 'RENTAL_GEOCODING_URL', '')
        if not url:
            return None
        timeout = aiohttp.ClientTimeout(total=getattr(settings, 'HTTP_TIMEOUT', 60))
        payload = dict(
            contract=getattr(settings, 'RENTAL_GEOCODING_CONTRACT', 'doverabot_rental_geocoding_v1'),
            query=address,
            limit=getattr(settings, 'RENTAL_GEOCODING_LIMIT', 3),
            source='telegram_rental',
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=cls.geocoding_headers(), json=payload) as resp:
                if resp.status >= 400:
                    logging.warning('rental geocoding failed with status %s', resp.status)
                    return None
                return await resp.json(content_type=None)

    @classmethod
    def geocode_suggestions_from_response(cls, data, limit=None):
        limit = limit or getattr(settings, 'RENTAL_GEOCODING_LIMIT', 3)
        if not data:
            return []
        candidates = data
        if isinstance(data, dict):
            candidates = (
                data.get('results') or
                data.get('suggestions') or
                data.get('items') or
                data.get('features') or
                data.get('result') or
                data.get('data') or
                []
            )
        if isinstance(candidates, dict):
            candidates = [candidates]
        if not isinstance(candidates, list):
            return []
        suggestions = []
        seen = set()
        for item in candidates:
            if not isinstance(item, dict):
                continue
            geometry = item.get('geometry') or {}
            properties = item.get('properties') or {}
            coordinates = geometry.get('coordinates') if isinstance(geometry, dict) else None
            lat = (
                item.get('latitude') or item.get('lat') or
                properties.get('latitude') or properties.get('lat')
            )
            lon = (
                item.get('longitude') or item.get('lng') or item.get('lon') or
                properties.get('longitude') or properties.get('lng') or properties.get('lon')
            )
            if lat is None and isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
                lon, lat = coordinates[0], coordinates[1]
            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            label = (
                item.get('label') or item.get('title') or item.get('name') or
                item.get('display_name') or item.get('formatted') or item.get('address') or
                properties.get('label') or properties.get('name') or properties.get('address') or
                'Адрес'
            )
            address = item.get('address') or properties.get('address') or label
            dedupe_key = (round(lat, 6), round(lon, 6), str(label))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            suggestions.append(dict(
                label=str(label).strip(),
                address=str(address).strip(),
                latitude=lat,
                longitude=lon,
            ))
            if len(suggestions) >= limit:
                break
        return suggestions

    @classmethod
    async def geocode_address(cls, address):
        address = (address or '').strip()
        if not address or not getattr(settings, 'RENTAL_GEOCODING_URL', ''):
            return []
        try:
            data = await cls.geocode_provider_request(address)
        except Exception:
            logging.exception('rental geocoding request failed')
            return []
        return cls.geocode_suggestions_from_response(data)

    @classmethod
    def geocode_callback_data(cls, flow, action, index=0):
        return '%s%s%s%s%s%s%s' % (
            KeyboardType.RENTAL_GEOCODE,
            KeyboardType.SEP,
            flow,
            KeyboardType.SEP,
            action,
            KeyboardType.SEP,
            index,
        )

    @classmethod
    def parse_geocode_callback_data(cls, callback):
        parts = (callback.data or '').split(KeyboardType.SEP)
        if (
            len(parts) != 4 or
            parts[0] != str(KeyboardType.RENTAL_GEOCODE) or
            parts[1] not in cls.GEOCODE_FLOWS or
            parts[2] not in {cls.ACTION_GEOCODE_USE, cls.ACTION_GEOCODE_SKIP} or
            not parts[3].isdigit()
        ):
            return '', '', 0
        return parts[1], parts[2], int(parts[3])

    @classmethod
    def text_geocode_label(cls, suggestion):
        label = suggestion.get('label') or suggestion.get('address') or 'Адрес'
        return label[:57] + '...' if len(label) > 60 else label

    @classmethod
    def markup_geocode(cls, flow, suggestions):
        rows = []
        for index, suggestion in enumerate(suggestions):
            rows.append([
                InlineKeyboardButton(
                    text=cls.text_geocode_label(suggestion),
                    callback_data=cls.geocode_callback_data(flow, cls.ACTION_GEOCODE_USE, index),
                )
            ])
        rows.append([
            InlineKeyboardButton(
                text='Без координат',
                callback_data=cls.geocode_callback_data(flow, cls.ACTION_GEOCODE_SKIP, 0),
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @classmethod
    def text_geocode_prompt(cls, address, suggestions):
        variants = '\n'.join(
            '%s. %s' % (index + 1, html.quote(cls.text_geocode_label(suggestion)))
            for index, suggestion in enumerate(suggestions)
        )
        return (
            'Нашлись варианты координат для адреса "%s".\n'
            '%s\n\n'
            'Выберите вариант, чтобы добавить координаты, или продолжите без координат.'
        ) % (html.quote(address), variants)

    @classmethod
    def coordinates_from_suggestion(cls, suggestion):
        return dict(
            latitude=suggestion['latitude'],
            longitude=suggestion['longitude'],
        )

    RU_MONTHS = {
        'января': 1,
        'январь': 1,
        'февраля': 2,
        'февраль': 2,
        'марта': 3,
        'март': 3,
        'апреля': 4,
        'апрель': 4,
        'мая': 5,
        'май': 5,
        'июня': 6,
        'июнь': 6,
        'июля': 7,
        'июль': 7,
        'августа': 8,
        'август': 8,
        'сентября': 9,
        'сентябрь': 9,
        'октября': 10,
        'октябрь': 10,
        'ноября': 11,
        'ноябрь': 11,
        'декабря': 12,
        'декабрь': 12,
    }
    RU_DAY_WORDS = {
        'первого': 1,
        'первое': 1,
        'первый': 1,
        'один': 1,
        'второго': 2,
        'второе': 2,
        'второй': 2,
        'два': 2,
        'третьего': 3,
        'третье': 3,
        'третий': 3,
        'три': 3,
        'четвертого': 4,
        'четвертое': 4,
        'четвертый': 4,
        'четыре': 4,
        'пятого': 5,
        'пятое': 5,
        'пятый': 5,
        'пять': 5,
        'шестого': 6,
        'шестое': 6,
        'шестой': 6,
        'шесть': 6,
        'седьмого': 7,
        'седьмое': 7,
        'седьмой': 7,
        'семь': 7,
        'восьмого': 8,
        'восьмое': 8,
        'восьмой': 8,
        'восемь': 8,
        'девятого': 9,
        'девятое': 9,
        'девятый': 9,
        'девять': 9,
        'десятого': 10,
        'десятое': 10,
        'десятый': 10,
        'десять': 10,
    }

    @classmethod
    def parse_day_value(cls, raw):
        raw = (raw or '').strip().lower().replace('ё', 'е')
        if raw.isdigit():
            day = int(raw)
            return day if 1 <= day <= 31 else None
        return cls.RU_DAY_WORDS.get(raw)

    @classmethod
    def parse_russian_date(cls, day_raw, month_raw, year_raw=''):
        day = cls.parse_day_value(day_raw)
        month = cls.RU_MONTHS.get((month_raw or '').strip().lower().replace('ё', 'е'))
        if not day or not month:
            return ''
        today = datetime.date.today()
        year = int(year_raw) if year_raw else today.year
        try:
            result = datetime.date(year, month, day)
        except ValueError:
            return ''
        if not year_raw and result < today - datetime.timedelta(days=31):
            try:
                result = result.replace(year=year + 1)
            except ValueError:
                return ''
        return result.isoformat()

    @classmethod
    def date_values_from_text(cls, text):
        values = []
        seen = set()

        def add(value):
            if value and value not in seen:
                values.append(value)
                seen.add(value)

        for value in re.findall(r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{4})\b', text):
            add(cls.parse_search_date(value))

        day_pattern = r'\d{1,2}|[а-яё]+'
        month_pattern = '|'.join(sorted(map(re.escape, cls.RU_MONTHS), key=len, reverse=True))
        range_pattern = (
            r'\bс\s+(%s)(?:\s+(%s))?\s+(?:по|до|[-–])\s+(%s)\s+(%s)(?:\s+(\d{4}))?'
            % (day_pattern, month_pattern, day_pattern, month_pattern)
        )
        for match in re.finditer(range_pattern, text, flags=re.I):
            month_start = match.group(2) or match.group(4)
            add(cls.parse_russian_date(match.group(1), month_start, match.group(5) or ''))
            add(cls.parse_russian_date(match.group(3), match.group(4), match.group(5) or ''))

        single_pattern = r'\b(%s)\s+(%s)(?:\s+(\d{4}))?\b' % (day_pattern, month_pattern)
        for match in re.finditer(single_pattern, text, flags=re.I):
            add(cls.parse_russian_date(match.group(1), match.group(2), match.group(3) or ''))

        return values

    @classmethod
    def clean_address_text(cls, text):
        text = (text or '').strip()
        text = re.split(
            r'\b(?:дат[аы]|доступн\w*|когда|сроки|цена|стоимост\w*|оплат\w*|руб\w*|₽)\b',
            text,
            maxsplit=1,
            flags=re.I,
        )[0]
        text = re.sub(
            r'^(?:можно|будет|это|в|на|у|около|рядом\s+с)\s+',
            '',
            text,
            flags=re.I,
        )
        return text.strip(' \t\n\r,.;:-')

    @classmethod
    def looks_like_spoken_address(cls, text):
        text = (text or '').strip(' \t\n\r,.;:-')
        if len(text) < 3:
            return False
        if re.search(
                r'\b(?:выходн\w*|будн\w*|день|дня|дней|недел\w*|месяц\w*|час\w*)\b',
                text,
                flags=re.I,
        ):
            return False
        return bool(re.search(
            (
                r'\b(?:парадром\w*|аэродром\w*|полигон\w*|парк\w*|метро|'
                r'станци\w*|улиц\w*|проспект\w*|площад\w*|шоссе|район\w*|'
                r'город\w*|деревн\w*|пос[её]л\w*|база\w*|клуб\w*|центр\w*|'
                r'склон\w*|трасс\w*|лагер\w*|вднх|москва|минск|сочи|спб|'
                r'санкт-петербург)\b'
            ),
            text,
            flags=re.I,
        ))

    @classmethod
    def extract_spoken_address(cls, text):
        before_price = re.split(
            r'\b(?:цена|стоимост\w*|оплат\w*|за\s+\d|руб\w*|₽)\b',
            text or '',
            maxsplit=1,
            flags=re.I,
        )[0]
        prep = r'(?:в|на|у|около|рядом\s+с)'
        pattern = r'\b%s\s+(.+?)(?=\s+\b%s\b|[,.;]|\n|$)' % (prep, prep)
        candidates = []
        for match in re.finditer(pattern, before_price, flags=re.I):
            address = cls.clean_address_text(match.group(1))
            if cls.looks_like_spoken_address(address):
                candidates.append(address)
        return candidates[-1] if candidates else ''

    @classmethod
    def extract_address(cls, text):
        patterns = (
            r'(?:адрес|где|место)\s*[:\-]\s*([^\n]+)',
            r'(?:адрес|место|локация)\s+(?:это\s+)?([^\n,.;]+)',
            r'(?:где\s+)?(?:забрать|самовывоз|выдача)\s*(?:можно\s*)?(?:[:\-]?\s*)?([^\n,.;]+)',
        )
        for pattern in patterns:
            if m := re.search(pattern, text, flags=re.I):
                address = cls.clean_address_text(m.group(1))
                if address:
                    return address
        address = cls.extract_spoken_address(text)
        if address:
            return address
        return ''

    @classmethod
    def clean_availability_text(cls, text):
        text = re.split(
            r'\b(?:цена|стоимост\w*|оплат\w*|адрес|место|забрать|самовывоз|выдача)\b|\bза\s+\d+',
            text or '',
            maxsplit=1,
            flags=re.I,
        )[0]
        return text.strip(' \t\n\r,.;:-')

    @classmethod
    def extract_spoken_availability(cls, text):
        text = (text or '').strip()
        if not text:
            return ''
        patterns = (
            r'\b(?:сегодня|завтра|послезавтра)\b[^\n,.;]*',
            r'\b(?:на|в|по)\s+(?:выходн\w*|будн\w*)[^\n,.;]*',
            r'\b(?:в\s+)?(?:любо[ей]|кажд\w+)\s+(?:время|день|дат\w*)[^\n,.;]*',
            r'\b(?:всегда|постоянно|ежедневно|круглосуточно|уже\s+доступн\w*|сейчас\s+доступн\w*)[^\n,.;]*',
            r'\b(?:до|на)\s+(?:конц\w+\s+)?(?:сезон\w*|лет\w*|зим\w*|осен\w*|весн\w*)[^\n,.;]*',
        )
        for pattern in patterns:
            if m := re.search(pattern, text, flags=re.I):
                availability = cls.clean_availability_text(m.group(0))
                if availability:
                    return availability
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
        address = cls.extract_address(text)
        quantity_total = ''
        if m := re.search(
                r'(?:количество|кол-во|шт\.?)\s*[:\-]?\s*(\d+)|(\d+)\s*(?:шт\.?|штук|единиц)',
                text,
                flags=re.I,
        ):
            quantity_total = m.group(1) or m.group(2) or ''
        latitude, longitude = Misc.check_location_str(text)
        date_values = cls.date_values_from_text(text)
        availability_text = ''
        if m := re.search(r'(?:даты|доступн\w*|когда|сроки)\s*[:\-]?\s*([^\n]+)', text, flags=re.I):
            availability_text = cls.clean_availability_text(m.group(1))
        elif date_values:
            availability_text = ' - '.join(date_values)
        else:
            availability_text = cls.extract_spoken_availability(text)
        return dict(
            title=title,
            item_text=title,
            description_text=text,
            price_text=price_text,
            availability_text=availability_text,
            available_from=date_values[0] if date_values else '',
            available_to=date_values[-1] if len(date_values) > 1 else '',
            quantity_total=quantity_total,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )

    @classmethod
    def merge_offer_slots(cls, current, new):
        merged = dict(current or {})
        for key, value in (new or {}).items():
            if value in (None, ''):
                continue
            if key in ('title', 'item_text') and merged.get(key):
                continue
            if key == 'description_text' and merged.get(key):
                if value not in merged[key]:
                    merged[key] = '%s\n%s' % (merged[key], value)
                continue
            merged[key] = value
        return merged

    @classmethod
    def offer_payload_slots(cls, slots):
        return {
            key: value
            for key, value in (slots or {}).items()
            if key in cls.LLM_OFFER_SLOT_KEYS and value not in (None, '')
        }

    @classmethod
    def offer_missing_fields(cls, slots):
        missing = []
        if not (slots.get('title') or slots.get('item_text')):
            missing.append('item')
        if not (
                slots.get('address') or
                (slots.get('latitude') is not None and slots.get('longitude') is not None)
        ):
            missing.append('place')
        if not (slots.get('availability_text') or slots.get('available_from') or slots.get('available_to')):
            missing.append('availability')
        if not (slots.get('price_text') or slots.get('price_amount')):
            missing.append('price')
        return missing

    @classmethod
    def offer_missing_prompt(cls, missing):
        labels = [
            cls.OFFER_MISSING_LABELS[item]
            for item in missing
            if item in cls.OFFER_MISSING_LABELS
        ]
        return 'Уточните: %s.' % '; '.join(labels)

    @classmethod
    def offer_debug_id(cls, data_or_uuid):
        if isinstance(data_or_uuid, dict):
            value = data_or_uuid.get('uuid_pack') or ''
        else:
            value = data_or_uuid or ''
        return str(value)[:8]

    @classmethod
    def bounded_text(cls, value, limit=900):
        value = str(value or '').strip()
        if limit and len(value) > limit:
            return value[:limit].rstrip() + '...'
        return value

    @classmethod
    def append_heard_text(cls, current, new_text):
        current = (current or '').strip()
        new_text = (new_text or '').strip()
        if not new_text:
            return current
        if not current:
            return new_text
        if new_text in current:
            return current
        return '%s\n%s' % (current, new_text)

    @classmethod
    def offer_missing_labels(cls, missing):
        labels = []
        for item in (missing or []):
            label = cls.OFFER_MISSING_LABELS.get(item, item)
            if label:
                labels.append(str(label))
        return labels

    @classmethod
    def offer_draft_field_lines(cls, slots):
        slots = slots or {}
        lines = []
        item = slots.get('item_text') or slots.get('title') or ''
        if item:
            lines.append('- Предмет: %s' % html.quote(cls.bounded_text(item, 180)))
        if slots.get('address'):
            lines.append('- Где: %s' % html.quote(cls.bounded_text(slots['address'], 180)))
        elif slots.get('latitude') is not None and slots.get('longitude') is not None:
            lines.append('- Где: %s, %s' % (slots['latitude'], slots['longitude']))
        availability = slots.get('availability_text') or ''
        if slots.get('available_from') or slots.get('available_to'):
            dates = '%s - %s' % (slots.get('available_from') or '?', slots.get('available_to') or '?')
            availability = ('%s %s' % (availability, dates)).strip()
        if availability:
            lines.append('- Когда: %s' % html.quote(cls.bounded_text(availability, 180)))
        price = slots.get('price_text') or ''
        if not price and slots.get('price_amount'):
            price = '%s %s %s' % (
                slots.get('price_amount') or '',
                slots.get('price_currency') or '',
                slots.get('price_period') or '',
            )
        if price:
            lines.append('- Цена: %s' % html.quote(cls.bounded_text(price, 180)))
        quantity = slots.get('quantity_total') or ''
        if str(quantity) not in ('', '1'):
            lines.append('- Количество: %s' % html.quote(str(quantity)))
        description = cls.bounded_text(slots.get('description_text') or '', 360)
        if description:
            lines.append('- Описание: %s' % html.quote(description))
        return lines

    @classmethod
    def text_offer_draft_preview(cls, heard_text, slots, missing, debug_id=''):
        heard_text = cls.bounded_text(heard_text, 900)
        if heard_text:
            result = 'Я услышал:\n“%s”\n\n' % html.quote(heard_text)
        else:
            result = 'Я пока не получил текст описания.\n\n'
        result += 'Черновик объявления:\n'
        field_lines = cls.offer_draft_field_lines(slots)
        result += '\n'.join(field_lines or ['- пока нет распознанных полей'])
        if missing:
            result += '\n\nНе хватает: %s.' % html.quote('; '.join(cls.offer_missing_labels(missing)))
            result += '\nМожно прислать исправление голосом/текстом или сохранить как черновик.'
        else:
            result += '\n\nВсе ключевые поля заполнены.'
            result += '\nМожно сохранить или прислать исправление голосом/текстом.'
        result += '\nПосле сохранения я попрошу фото/видео/документы.'
        if debug_id:
            result += '\n\nКод черновика: %s' % html.quote(debug_id)
        return result

    @classmethod
    def offer_draft_callback_data(cls, action):
        return '%s%s%s' % (
            KeyboardType.RENTAL_OFFER_DRAFT,
            KeyboardType.SEP,
            action,
        )

    @classmethod
    def parse_offer_draft_callback_data(cls, callback):
        parts = (callback.data or '').split(KeyboardType.SEP)
        if (
            len(parts) != 2 or
            parts[0] != str(KeyboardType.RENTAL_OFFER_DRAFT) or
            parts[1] not in cls.ACTIONS_OFFER_DRAFT
        ):
            return ''
        return parts[1]

    @classmethod
    def markup_offer_draft(cls, missing=None):
        missing = missing or []
        save_text = '✅ Сохранить черновик' if missing else '✅ Всё верно / сохранить'
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=save_text,
                callback_data=cls.offer_draft_callback_data(cls.ACTION_OFFER_DRAFT_CONFIRM),
            )],
            [InlineKeyboardButton(
                text='✏️ Исправить или дополнить',
                callback_data=cls.offer_draft_callback_data(cls.ACTION_OFFER_DRAFT_EDIT),
            )],
            [InlineKeyboardButton(
                text='❌ Отмена',
                callback_data=cls.offer_draft_callback_data(cls.ACTION_OFFER_DRAFT_CANCEL),
            )],
        ])

    @classmethod
    def markup_offer_media(cls):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='📎 Добавить фото/видео',
                callback_data=cls.offer_draft_callback_data(cls.ACTION_OFFER_DRAFT_MEDIA),
            )],
            [InlineKeyboardButton(
                text='✅ Готово без медиа',
                callback_data=cls.offer_draft_callback_data(cls.ACTION_OFFER_DRAFT_DONE),
            )],
        ])

    @classmethod
    def text_offer_media_prompt(cls, offer, missing=None, flow_id=''):
        status_value = (offer or {}).get('status') or 'active'
        if status_value == 'draft':
            result = 'Объявление сохранено как черновик.'
            missing_labels = cls.offer_missing_labels(missing or [])
            if missing_labels:
                result += ' Не хватает: %s.' % '; '.join(missing_labels)
            result += ' Активировать его можно позже через /rent_my.'
        else:
            result = 'Объявление проката сохранено.'
        result += '\n\nТеперь можно прикрепить фото, видео, документ или аудио: просто отправьте сюда медиа. Когда закончите, нажмите «Готово».'
        debug_id = cls.offer_debug_id(flow_id)
        if debug_id:
            result += '\n\nКод черновика: %s' % html.quote(debug_id)
        return result

    @classmethod
    async def reply_offer_draft_preview(cls, message, state, data, heard_text, slots, missing, new_slots=None):
        heard_text = cls.append_heard_text(data.get('rental_offer_heard_text'), heard_text)
        source_tgdesc = data.get('rental_offer_source_tgdesc')
        source_chat_id = data.get('rental_offer_source_chat_id') or message.chat.id
        source_message_id = data.get('rental_offer_source_message_id') or message.message_id
        source_media_group_id = data.get('rental_offer_source_media_group_id') or message.media_group_id
        update_source = not source_tgdesc or message.content_type in (
            ContentType.PHOTO,
            ContentType.VIDEO,
            ContentType.DOCUMENT,
            ContentType.AUDIO,
            ContentType.VOICE,
        )
        if update_source:
            source_tgdesc = TgDesc.from_message(message, data['uuid_pack'])
            source_chat_id = message.chat.id
            source_message_id = message.message_id
            source_media_group_id = message.media_group_id
        debug_id = cls.offer_debug_id(data)
        await state.update_data(
            rental_slots=slots,
            rental_offer_heard_text=heard_text,
            rental_offer_missing_fields=missing,
            rental_offer_draft_status='preview',
            rental_offer_source_tgdesc=source_tgdesc,
            rental_offer_source_chat_id=source_chat_id,
            rental_offer_source_message_id=source_message_id,
            rental_offer_source_media_group_id=source_media_group_id,
        )
        cls.log_debug(
            'offer_draft_preview',
            message,
            flow_id=data.get('uuid_pack'),
            debug_id=debug_id,
            heard_len=len(heard_text or ''),
            new_slots=new_slots or {},
            merged_slots=slots,
            missing=missing,
            prompt_type='draft_preview',
        )
        await message.reply(
            cls.text_offer_draft_preview(heard_text, slots, missing, debug_id=debug_id),
            reply_markup=cls.markup_offer_draft(missing),
        )

    @classmethod
    def pending_offer_from_draft(cls, message, profile_from, data, slots, missing):
        status_value = 'draft' if missing else 'active'
        source_message_id = data.get('rental_offer_source_message_id') or message.message_id
        payload = dict(
            user_uuid=profile_from['uuid'],
            visibility='authenticated',
            status=status_value,
            tgdesc=data.get('rental_offer_source_tgdesc') or TgDesc.from_message(message, data['uuid_pack']),
        )
        payload.update(cls.offer_payload_slots(slots))
        return dict(
            payload=payload,
            rental_offer_uuid=data.get('rental_offer_uuid') or '',
            source_chat_id=data.get('rental_offer_source_chat_id') or message.chat.id,
            source_message_id=source_message_id,
            cache_key='%s%s%s%s%s' % (
                Rcache.RENTAL_DESC_PREFIX,
                Rcache.KEY_SEP,
                data['uuid_pack'],
                Rcache.KEY_SEP,
                source_message_id,
            ),
            is_first=True,
            media_group_id=data.get('rental_offer_source_media_group_id') or '',
            after_save='await_media',
            saved_status=status_value,
            missing=missing or [],
            flow_id=data.get('uuid_pack'),
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
        date_values = cls.date_values_from_text(text)
        latitude, longitude = Misc.check_location_str(text)
        price_max = ''
        if m := re.search(
                r'(?:до|<=|не дороже|макс(?:имум)?)\s*(\d[\d\s\.,]*)\s*(?:руб\.?|р\.?|₽|usd|eur|byn|долл\.?)?',
                text,
                flags=re.I,
        ):
            price_max = re.sub(r'\s+', '', m.group(1)).replace(',', '.')
        trusted_only = bool(re.search(r'\b(доверенн\w*|trusted|своих|свои)\b', text, flags=re.I))
        map_intent = bool(re.search(r'\b(карта|карте|map)\b', text, flags=re.I))
        address = ''
        if m := re.search(r'(?:адрес|где|место)\s*[:\-]\s*([^\n]+)', text, flags=re.I):
            address = m.group(1).strip()
        has_context = bool(date_values or latitude is not None or price_max or trusted_only or re.search(
            r'\b(адрес|где|место|город|метро|улица|рядом|москва|минск|сочи|спб|санкт-петербург)\b',
            text,
            flags=re.I,
        ))
        return dict(
            query=text.strip(),
            date_from=date_values[0] if date_values else '',
            date_to=date_values[-1] if len(date_values) > 1 else '',
            price_max=price_max,
            trusted_only=trusted_only,
            map_intent=map_intent,
            address=address,
            latitude=latitude,
            longitude=longitude,
            has_context=has_context,
        )

    @classmethod
    async def cmd_rent(cls, message: Message, state: FSMContext):
        text = cls.command_args(message, 'rent')
        if text:
            intent = cls.classify_rent_intro(text)
            if intent == 'offer':
                await cls.start_offer_flow(message, state, text)
                return
            if intent == 'search':
                await state.set_state(FSMRentalSearch.ask)
                await cls.handle_search_text(message, state, text)
                return
        await state.set_state(FSMRentalIntro.ask)
        await message.reply(cls.PROMPT_RENT_INTRO, reply_markup=Misc.reply_markup_cancel_row())

    @classmethod
    async def cmd_rent_offer(cls, message: Message, state: FSMContext):
        text = cls.command_args(message, 'rent_offer')
        await cls.start_offer_flow(message, state, text)

    @classmethod
    async def start_offer_flow(cls, message: Message, state: FSMContext, text=''):
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        await state.set_state(FSMRentalOffer.ask)
        await state.update_data(
            user_uuid=response_sender['uuid'],
            uuid_pack=str(uuid4()),
        )
        if text:
            await cls.handle_offer_text(
                message,
                state,
                response_sender,
                await state.get_data(),
                text,
            )
            return
        await message.reply(cls.offer_prompt(), reply_markup=Misc.reply_markup_cancel_row())

    @classmethod
    async def handle_offer_text(cls, message, state, profile_from, data, text):
        new_slots = await cls.extract_offer_slots(
            text,
            message=message,
            current_slots=data.get('rental_slots') or {},
        )
        slots = cls.merge_offer_slots(
            data.get('rental_slots') or {},
            new_slots,
        )
        for key in ('latitude', 'longitude'):
            if slots.get(key) is None and data.get(key) is not None:
                slots[key] = data[key]
        missing = cls.offer_missing_fields(slots)
        cls.log_debug(
            'offer_slots',
            message,
            flow_id=data.get('uuid_pack'),
            debug_id=cls.offer_debug_id(data),
            text=text,
            new_slots=new_slots,
            merged_slots=slots,
            missing=missing,
        )
        await cls.reply_offer_draft_preview(
            message,
            state,
            data,
            text,
            slots,
            missing,
            new_slots=new_slots,
        )

    @classmethod
    async def cmd_rent_search(cls, message: Message, state: FSMContext):
        query = cls.command_args(message, 'rent_search')
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
    async def search_with_params(cls, query, user_uuid, date_from='', date_to='',
                                 price_max='', trusted_only=False, map_intent=False,
                                 latitude=None, longitude=None):
        params = dict(query=query, user_uuid=user_uuid, number=5)
        if date_from:
            params.update(date_from=date_from)
        if date_to:
            params.update(date_to=date_to)
        if price_max:
            params.update(price_max=price_max)
        if trusted_only:
            params.update(trusted_only='on')
        if map_intent:
            params.update(map_intent='on')
        if latitude is not None and longitude is not None:
            delta = float(getattr(settings, 'RENTAL_GEOCODING_SEARCH_DELTA', 0.05) or 0.05)
            params.update(
                lat_south=latitude - delta,
                lat_north=latitude + delta,
                lng_west=longitude - delta,
                lng_east=longitude + delta,
            )
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
        quantity = offer.get('quantity_total') or ''
        if str(quantity) not in ('', '1'):
            result += '\nКоличество: %s\n' % html.quote(str(quantity))
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
    def markup_offer(cls, profile_from, offer, map_params=None):
        if profile_from and profile_from.get('uuid') == offer.get('owner', {}).get('uuid'):
            return None
        map_url = cls.get_map_url(offer, map_params=map_params)
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
                    url=map_url,
                )
            ]] if map_url else []),
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
        quantity = offer.get('quantity_total') or ''
        if str(quantity) not in ('', '1'):
            result += 'Количество: %s\n' % html.quote(str(quantity))
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
        map_url = cls.get_map_url(offer)
        if map_url:
            rows.append([
                InlineKeyboardButton(
                    text='На карте',
                    url=map_url,
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
        offer = response.get('offer') or {}
        if response.get('viewer_role') == 'owner':
            markup = cls.markup_reservation_owner(reservation)
        else:
            markup = cls.markup_reservation_consumer(reservation)
        rows = list(markup.inline_keyboard) if markup else []
        map_url = cls.get_map_url(offer, map_params=dict(
            date_from=reservation.get('date_from') or '',
            date_to=reservation.get('date_to') or '',
        ))
        if map_url:
            rows.append([
                InlineKeyboardButton(
                    text='На карте',
                    url=map_url,
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

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
    async def show_offer(cls, message, profile_from, offer, message_kind='search_result', map_params=None):
        reply_markup = cls.markup_offer(profile_from, offer, map_params=map_params)
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
    async def send_search_results_for_profile(cls, message, profile_from, query, date_from='', date_to='',
                                              price_max='', trusted_only=False, map_intent=False,
                                              latitude=None, longitude=None):
        search_kwargs = dict(
            date_from=date_from,
            date_to=date_to,
            price_max=price_max,
            trusted_only=trusted_only,
            map_intent=map_intent,
        )
        if latitude is not None and longitude is not None:
            search_kwargs.update(latitude=latitude, longitude=longitude)
        status, response = await cls.search_with_params(
            query,
            profile_from['uuid'],
            **search_kwargs,
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
        result_map_params = dict(
            query=query,
            date_from=date_from,
            date_to=date_to,
            price_max=price_max,
            trusted_only=trusted_only,
        )
        for offer in offers:
            await cls.show_offer(message, profile_from, offer, map_params=result_map_params)

    @classmethod
    async def send_search_results(cls, message, query, date_from='', date_to='',
                                  price_max='', trusted_only=False, map_intent=False,
                                  latitude=None, longitude=None):
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        await cls.send_search_results_for_profile(
            message,
            response_sender,
            query,
            date_from=date_from,
            date_to=date_to,
            price_max=price_max,
            trusted_only=trusted_only,
            map_intent=map_intent,
            latitude=latitude,
            longitude=longitude,
        )

    @classmethod
    async def maybe_prompt_offer_geocode(cls, message, state, slots, pending_offer):
        if (
            slots.get('latitude') is not None and slots.get('longitude') is not None
        ) or not slots.get('address'):
            return False
        data = await state.get_data()
        if data.get('rental_geocode_status') in ('confirmed', 'skipped', 'failed'):
            return False
        suggestions = await cls.geocode_address(slots['address'])
        if not suggestions:
            await state.update_data(rental_geocode_status='failed')
            return False
        await state.update_data(
            rental_slots=slots,
            pending_rental_geocode=dict(
                flow='offer',
                address=slots['address'],
                suggestions=suggestions,
            ),
            pending_rental_offer=pending_offer,
        )
        await message.reply(
            cls.text_geocode_prompt(slots['address'], suggestions),
            reply_markup=cls.markup_geocode('offer', suggestions),
        )
        return True

    @classmethod
    async def maybe_prompt_search_geocode(cls, message, state, params):
        if (
            params.get('latitude') is not None and params.get('longitude') is not None
        ) or not params.get('address'):
            return False
        data = await state.get_data()
        if data.get('rental_geocode_status') in ('confirmed', 'skipped', 'failed'):
            return False
        suggestions = await cls.geocode_address(params['address'])
        if not suggestions:
            await state.update_data(rental_geocode_status='failed')
            return False
        await state.update_data(
            query=params['query'],
            context_text=params.get('context_text', ''),
            date_from=params.get('date_from', ''),
            date_to=params.get('date_to', ''),
            price_max=params.get('price_max', ''),
            trusted_only=params.get('trusted_only', False),
            map_intent=params.get('map_intent', False),
            has_context=True,
            pending_rental_geocode=dict(
                flow='search',
                address=params['address'],
                suggestions=suggestions,
            ),
        )
        await message.reply(
            cls.text_geocode_prompt(params['address'], suggestions),
            reply_markup=cls.markup_geocode('search', suggestions),
        )
        return True

    @classmethod
    async def attach_offer_media(cls, message, state, profile_from, data):
        offer_uuid = data.get('rental_offer_uuid') or ''
        if not offer_uuid:
            await message.reply('Черновик уже не найден. Откройте создание заново через /rent_offer.')
            await state.clear()
            return
        pack_id = message.media_group_id or message.message_id
        cache_key = '%s%s%s%smedia%s%s' % (
            Rcache.RENTAL_DESC_PREFIX,
            Rcache.KEY_SEP,
            data.get('uuid_pack') or offer_uuid,
            Rcache.KEY_SEP,
            Rcache.KEY_SEP,
            pack_id,
        )
        is_first = Misc.redis_is_key_first_up(cache_key)
        if is_first is None:
            is_first = True
        payload = dict(
            user_uuid=profile_from['uuid'],
            offer_uuid=offer_uuid,
            tgdesc=TgDesc.from_message(message, data.get('uuid_pack') or str(uuid4())),
            is_first=False,
        )
        status, response = await cls.put_offer(payload)
        cls.log_debug(
            'offer_media_attached',
            message,
            flow_id=data.get('uuid_pack'),
            debug_id=cls.offer_debug_id(data),
            offer_uuid=offer_uuid,
            status=status,
            file_type=(payload.get('tgdesc') or {}).get('file_type'),
            media_group_id=message.media_group_id,
            prompt_type='media_attach',
        )
        if status != 200:
            await message.reply((response or {}).get('message') or 'Не удалось прикрепить медиа')
            return
        if not is_first:
            return
        if message.media_group_id:
            wait_last = await Misc.redis_wait_last_in_pack(cache_key)
            if wait_last is False:
                return
        await state.update_data(rental_offer_uuid=offer_uuid, rental_offer_media_mode=True)
        await message.reply(
            'Медиа прикреплено к объявлению. Можно отправить ещё или нажать «Готово».',
            reply_markup=cls.markup_offer_media(),
        )

    @classmethod
    async def save_offer_from_payload(cls, message, state, profile_from, pending_offer):
        payload = dict(pending_offer['payload'])
        if pending_offer.get('rental_offer_uuid'):
            payload.update(
                offer_uuid=pending_offer['rental_offer_uuid'],
                is_first=False,
            )
            status, response = await cls.put_offer(payload)
        else:
            status, response = await cls.create_offer(payload)
            if status == 200:
                await state.update_data(rental_offer_uuid=response['offer']['uuid'])
        if status != 200:
            await message.reply((response or {}).get('message') or 'Не удалось сохранить объявление')
            await state.clear()
            return
        offer = response['offer']
        cls.log_debug(
            'offer_saved',
            message,
            flow_id=pending_offer.get('flow_id'),
            debug_id=cls.offer_debug_id(pending_offer.get('flow_id')),
            offer_uuid=offer['uuid'],
            offer_status=offer.get('status') or pending_offer.get('saved_status'),
            missing=pending_offer.get('missing') or [],
            prompt_type='saved_media_prompt' if pending_offer.get('after_save') == 'await_media' else 'saved',
        )
        await cls.register_message(
            offer['uuid'],
            'owner_offer',
            pending_offer['source_chat_id'],
            pending_offer['source_message_id'],
            recipient_uuid=profile_from['uuid'],
        )
        if not pending_offer.get('is_first', True):
            return
        if pending_offer.get('media_group_id'):
            wait_last = await Misc.redis_wait_last_in_pack(pending_offer['cache_key'])
            if wait_last is False:
                return
        if pending_offer.get('after_save') == 'await_media':
            await state.set_state(FSMRentalOffer.ask)
            await state.update_data(
                rental_offer_uuid=offer['uuid'],
                rental_offer_media_mode=True,
                rental_offer_saved_status=offer.get('status') or pending_offer.get('saved_status') or 'active',
                pending_rental_offer={},
                pending_rental_geocode={},
                rental_geocode_status='confirmed' if offer.get('latitude') is not None else '',
            )
            await message.reply(
                cls.text_offer_media_prompt(
                    offer,
                    missing=pending_offer.get('missing') or [],
                    flow_id=pending_offer.get('flow_id') or '',
                ),
                reply_markup=cls.markup_offer_media(),
            )
            return
        await state.clear()
        await message.reply('Объявление проката сохранено')
        await cls.show_offer(message, profile_from, offer)

    @classmethod
    async def handle_search_text(cls, message, state, text):
        data = await state.get_data()
        slots = await cls.extract_search_slots_with_llm(text, message=message, current_slots=data)
        cls.log_debug(
            'search_slots',
            message,
            text=text,
            slots=slots,
            state_data=data,
        )
        query = data.get('query') or slots['query']
        context_text = data.get('context_text') or ''
        date_from = data.get('date_from') or slots['date_from']
        date_to = data.get('date_to') or slots['date_to']
        price_max = data.get('price_max') or slots['price_max']
        trusted_only = bool(data.get('trusted_only') or slots['trusted_only'])
        map_intent = bool(data.get('map_intent') or slots['map_intent'])
        has_context = bool(data.get('has_context') or slots['has_context'])
        address = data.get('address') or slots['address']
        latitude = data.get('latitude') if data.get('latitude') is not None else slots['latitude']
        longitude = data.get('longitude') if data.get('longitude') is not None else slots['longitude']
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
                price_max=price_max,
                trusted_only=trusted_only,
                map_intent=map_intent,
                address=address,
                has_context=False,
            )
            await message.reply(cls.search_context_prompt(), reply_markup=Misc.reply_markup_cancel_row())
            return
        search_query = ('%s %s' % (query, context_text)).strip()
        if await cls.maybe_prompt_search_geocode(message, state, dict(
                query=query,
                context_text=context_text,
                date_from=date_from,
                date_to=date_to,
                price_max=price_max,
                trusted_only=trusted_only,
                map_intent=map_intent,
                address=address,
                latitude=latitude,
                longitude=longitude,
        )):
            return
        await state.clear()
        await cls.send_search_results(
            message,
            search_query,
            date_from=date_from,
            date_to=date_to,
            price_max=price_max,
            trusted_only=trusted_only,
            map_intent=map_intent,
            latitude=latitude,
            longitude=longitude,
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


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMRentalIntro.ask))
async def process_rental_intro(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    text = await Rental.message_or_voice_text(message)
    if message.content_type == ContentType.VOICE and not text:
        logging.info(
            'rental intro voice was not recognized, user_id=%s chat_id=%s message_id=%s',
            message.from_user.id,
            message.chat.id,
            message.message_id,
        )
        await message.reply(
            'Голосовое не распознано. Пришлите одним сообщением текстом или голосом: «ищу ...» или «сдам ...».',
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        return
    if not text:
        await message.reply(Rental.PROMPT_RENT_INTRO, reply_markup=Misc.reply_markup_cancel_row())
        return
    intent = Rental.classify_rent_intro(text)
    if intent == 'offer':
        await Rental.start_offer_flow(message, state, text)
        return
    if intent == 'search':
        await state.set_state(FSMRentalSearch.ask)
        await Rental.handle_search_text(message, state, text)
        return
    await message.reply(
        'Не понял: вы хотите сдать вещь или найти в аренду? Напишите или скажите одним сообщением: «сдам ...» или «ищу ...».',
        reply_markup=Misc.reply_markup_cancel_row(),
    )


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMRentalOffer.ask))
async def process_rental_offer(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if status_from != 200 or profile_from['uuid'] != data.get('user_uuid'):
        await state.clear()
        return
    if data.get('rental_offer_media_mode'):
        if message.content_type in Rental.OFFER_MEDIA_CONTENT_TYPES:
            await Rental.attach_offer_media(message, state, profile_from, data)
            return
        done_text = Rental.message_text(message).lower()
        if done_text in ('готово', 'готово без медиа', 'без медиа', 'всё', 'все'):
            await state.clear()
            await message.reply('Готово. Управлять объявлениями можно через /rent_my.')
            return
        await message.reply(
            'Объявление уже сохранено. Пришлите фото/видео/документ/аудио или нажмите «Готово».',
            reply_markup=Rental.markup_offer_media(),
        )
        return
    if message.content_type == ContentType.LOCATION and message.location:
        slots = Rental.merge_offer_slots(data.get('rental_slots') or {}, dict(
            latitude=message.location.latitude,
            longitude=message.location.longitude,
        ))
        missing = Rental.offer_missing_fields(slots)
        await state.update_data(
            latitude=message.location.latitude,
            longitude=message.location.longitude,
            rental_slots=slots,
        )
        await Rental.reply_offer_draft_preview(
            message,
            state,
            data,
            'Геолокация: %s, %s' % (message.location.latitude, message.location.longitude),
            slots,
            missing,
            new_slots=dict(latitude=message.location.latitude, longitude=message.location.longitude),
        )
        return
    text = await Rental.message_or_voice_text(message)
    if message.content_type == ContentType.VOICE and not text:
        logging.info(
            'rental offer voice was not recognized, user_id=%s chat_id=%s message_id=%s',
            message.from_user.id,
            message.chat.id,
            message.message_id,
        )
        Rental.log_debug(
            'offer_voice_unrecognized',
            message,
            flow_id=data.get('uuid_pack'),
            debug_id=Rental.offer_debug_id(data),
            prompt_type='voice_unrecognized',
        )
        await message.reply(
            'Голосовое не распознано. Пришлите описание текстом или попробуйте другое голосовое.',
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        return
    if not text:
        await message.reply(Rental.offer_prompt(), reply_markup=Misc.reply_markup_cancel_row())
        return
    await Rental.handle_offer_text(message, state, profile_from, data, text)


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
        KeyboardType.RENTAL_OFFER_DRAFT,
        KeyboardType.SEP,
    )))
async def cbq_rental_offer_draft(callback: CallbackQuery, state: FSMContext):
    action = Rental.parse_offer_draft_callback_data(callback)
    if not action:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if (
        status_from != 200 or
        not data.get('user_uuid') or
        profile_from['uuid'] != data.get('user_uuid')
    ):
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_AUTH)
        return
    if action == Rental.ACTION_OFFER_DRAFT_CANCEL:
        await state.clear()
        await callback.message.reply('Черновик объявления отменён.')
        await callback.answer('Отменено')
        return
    if action == Rental.ACTION_OFFER_DRAFT_EDIT:
        await state.set_state(FSMRentalOffer.ask)
        await state.update_data(rental_offer_draft_status='editing')
        await callback.message.reply(
            'Пришлите исправление или дополнение голосом/текстом: например «цена 1500, залог 5000».'
        )
        await callback.answer('Жду исправление')
        return
    if action == Rental.ACTION_OFFER_DRAFT_DONE:
        if not data.get('rental_offer_uuid'):
            await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
            return
        await state.clear()
        await callback.message.reply('Готово. Управлять объявлениями можно через /rent_my.')
        await callback.answer('Готово')
        return
    if action == Rental.ACTION_OFFER_DRAFT_MEDIA:
        if not data.get('rental_offer_uuid'):
            await Rental.answer_callback_notice(callback, 'Сначала сохраните черновик объявления.')
            return
        await state.set_state(FSMRentalOffer.ask)
        await state.update_data(rental_offer_media_mode=True)
        await callback.message.reply(
            'Пришлите фото, видео, документ или аудио следующим сообщением.',
            reply_markup=Rental.markup_offer_media(),
        )
        await callback.answer('Жду медиа')
        return
    if data.get('rental_offer_media_mode'):
        await callback.answer('Объявление уже сохранено')
        return
    slots = dict(data.get('rental_slots') or {})
    if not slots:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
        return
    missing = data.get('rental_offer_missing_fields') or Rental.offer_missing_fields(slots)
    pending_offer = Rental.pending_offer_from_draft(callback.message, profile_from, data, slots, missing)
    if await Rental.maybe_prompt_offer_geocode(callback.message, state, slots, pending_offer):
        await callback.answer('Проверьте координаты')
        return
    await Rental.save_offer_from_payload(callback.message, state, profile_from, pending_offer)
    await callback.answer('Сохранено')


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.RENTAL_GEOCODE,
        KeyboardType.SEP,
    )))
async def cbq_rental_geocode(callback: CallbackQuery, state: FSMContext):
    flow, action, index = Rental.parse_geocode_callback_data(callback)
    data = await state.get_data()
    pending = data.get('pending_rental_geocode') or {}
    suggestions = pending.get('suggestions') or []
    if not flow or pending.get('flow') != flow or (action == Rental.ACTION_GEOCODE_USE and index >= len(suggestions)):
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
        return
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_AUTH)
        return
    coords = {}
    if action == Rental.ACTION_GEOCODE_USE:
        coords = Rental.coordinates_from_suggestion(suggestions[index])
    if flow == 'offer':
        pending_offer = data.get('pending_rental_offer') or {}
        if not pending_offer:
            await Rental.answer_callback_notice(callback, Rental.MSG_CALLBACK_STALE)
            return
        slots = dict(data.get('rental_slots') or {})
        payload = dict(pending_offer.get('payload') or {})
        if coords:
            slots.update(coords)
            payload.update(coords)
        pending_offer['payload'] = payload
        await state.update_data(
            rental_slots=slots,
            rental_geocode_status='confirmed' if coords else 'skipped',
            pending_rental_geocode={},
            pending_rental_offer=pending_offer,
        )
        await Rental.save_offer_from_payload(callback.message, state, profile_from, pending_offer)
        await callback.answer('Координаты добавлены' if coords else 'Продолжаю без координат')
        return
    search_query = ('%s %s' % (data.get('query') or '', data.get('context_text') or '')).strip()
    await state.clear()
    await Rental.send_search_results_for_profile(
        callback.message,
        profile_from,
        search_query,
        date_from=data.get('date_from') or '',
        date_to=data.get('date_to') or '',
        price_max=data.get('price_max') or '',
        trusted_only=bool(data.get('trusted_only')),
        map_intent=bool(data.get('map_intent')),
        latitude=coords.get('latitude'),
        longitude=coords.get('longitude'),
    )
    await callback.answer('Ищу рядом с выбранным адресом' if coords else 'Ищу без координат')


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
