import asyncio
import html as std_html
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


BOT_DIR = Path(__file__).resolve().parents[1]
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))


class FilterStub:
    def __getattr__(self, _name):
        return self

    def __call__(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def regexp(self, *_args, **_kwargs):
        return self


class RouterStub:
    def message(self, *_args, **_kwargs):
        return lambda func: func

    def callback_query(self, *_args, **_kwargs):
        return lambda func: func


class InlineKeyboardButtonStub:
    def __init__(self, text, callback_data=None, url=None, **kwargs):
        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.kwargs = kwargs


class InlineKeyboardMarkupStub:
    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard


class ContentTypeStub:
    TEXT = 'text'
    VOICE = 'voice'
    PHOTO = 'photo'
    VIDEO = 'video'
    DOCUMENT = 'document'
    AUDIO = 'audio'
    LOCATION = 'location'


class ChatTypeStub:
    PRIVATE = 'private'
    GROUP = 'group'
    SUPERGROUP = 'supergroup'


class TelegramBadRequestStub(Exception):
    pass


class TelegramForbiddenErrorStub(Exception):
    pass


class TelegramNetworkErrorStub(Exception):
    pass


class StateStub:
    pass


class StatesGroupStub:
    pass


class MemoryStorageStub:
    pass


class RedisStorageStub:
    def __init__(self, redis=None, key_builder=None):
        self.redis = redis
        self.key_builder = key_builder


class DefaultKeyBuilderStub:
    def __init__(self, prefix='fsm', with_bot_id=False):
        self.prefix = prefix
        self.with_bot_id = with_bot_id


class RedisClientStub:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DispatcherStub:
    def __init__(self, storage=None):
        self.storage = storage

    def include_routers(self, *_routers):
        pass

    async def start_polling(self, *_args, **_kwargs):
        pass


class BotStub:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def get_me(self):
        return types.SimpleNamespace(username='DoveraBot')

    async def delete_webhook(self, **_kwargs):
        pass


def install_dependency_stubs(stub_common=True):
    settings = types.ModuleType('settings')
    settings.TOKEN = '123:test'
    settings.HTTP_TIMEOUT = 60
    settings.API_HOST = 'https://api.doverabot.ru'
    settings.MAP_HOST = 'https://map.doverabot.ru'
    settings.GRAPH_HOST = 'https://d3.doverabot.ru'
    settings.GRAPH_MEET_HOST = 'https://mgraph.doverabot.ru'
    settings.MEET_HOST = 'https://doverabot.ru'
    settings.FRONTEND_HOST = 'https://doverabot.ru'
    settings.FRONTEND_AUTH_PATH = 'auth/telegram/'
    settings.SHORT_ID_LINK = 'doverabot.ru/t/%s'
    settings.BOT_ADMINS = []
    settings.GROUPS_WITH_CARDS = {}
    settings.MIN_LEN_SEARCHED_TEXT = 3
    settings.DOWNLOAD_PHOTO_MAX_SIZE = 10
    settings.PHOTO_MAX_SIZE = 1024 * 1024
    settings.MULTI_MESSAGE_TIMEOUT = 60
    settings.REDIS_SET_NEXT_SYMPA_WAIT = 60
    settings.OFFER_MAX_NUM_ANSWERS = 10
    settings.RENTAL_STT_CONTRACT = 'organizm_hermes_v1'
    settings.RENTAL_STT_URL = 'https://hermes.example/transcribe'
    settings.RENTAL_STT_TOKEN = 'stt-token'
    settings.RENTAL_STT_MODE = 'file_id'
    settings.RENTAL_STT_LANGUAGE = 'ru'
    settings.REDIS_CONNECT = dict(host='127.0.0.1', port=6379, db=2, decode_responses=True)
    settings.BOT_FSM_STORAGE = 'redis'
    settings.BOT_FSM_REDIS_CONNECT = settings.REDIS_CONNECT.copy()
    settings.BOT_FSM_REDIS_PREFIX = 'doverabot:fsm'
    settings.BOT_FSM_REDIS_FALLBACK_TO_MEMORY = False
    settings.LOCAL_SERVER = None
    settings.PROXY = None
    settings.SCHEDULE_CRON = {}
    sys.modules['settings'] = settings

    me = types.ModuleType('me')
    me.dp = None
    me.bot = None
    me.bot_data = types.SimpleNamespace(username='DoveraBot')
    sys.modules['me'] = me

    aiogram = types.ModuleType('aiogram')
    aiogram.__path__ = []
    aiogram.Router = RouterStub
    aiogram.F = FilterStub()
    aiogram.html = types.SimpleNamespace(quote=std_html.escape)
    aiogram.Bot = BotStub
    aiogram.Dispatcher = DispatcherStub
    aiogram.enums = types.SimpleNamespace(ParseMode=types.SimpleNamespace(HTML='HTML'))
    sys.modules['aiogram'] = aiogram

    aiogram_client = types.ModuleType('aiogram.client')
    aiogram_client.__path__ = []
    sys.modules['aiogram.client'] = aiogram_client

    aiogram_client_session = types.ModuleType('aiogram.client.session')
    aiogram_client_session.__path__ = []
    sys.modules['aiogram.client.session'] = aiogram_client_session

    aiogram_fsm = types.ModuleType('aiogram.fsm')
    aiogram_fsm.__path__ = []
    sys.modules['aiogram.fsm'] = aiogram_fsm

    aiogram_fsm_storage = types.ModuleType('aiogram.fsm.storage')
    aiogram_fsm_storage.__path__ = []
    sys.modules['aiogram.fsm.storage'] = aiogram_fsm_storage

    filters = types.ModuleType('aiogram.filters')
    filters.Command = lambda *_args, **_kwargs: None
    filters.CommandStart = lambda *_args, **_kwargs: None
    filters.CommandObject = object
    filters.StateFilter = lambda *_args, **_kwargs: None
    sys.modules['aiogram.filters'] = filters

    filters_logic = types.ModuleType('aiogram.filters.logic')
    filters_logic.or_f = lambda *_args, **_kwargs: None
    sys.modules['aiogram.filters.logic'] = filters_logic

    types_mod = types.ModuleType('aiogram.types')
    types_mod.__path__ = []
    types_mod.Message = object
    types_mod.CallbackQuery = object
    types_mod.ContentType = ContentTypeStub
    types_mod.InlineKeyboardMarkup = InlineKeyboardMarkupStub
    types_mod.InlineKeyboardButton = InlineKeyboardButtonStub
    types_mod.BufferedInputFile = lambda *args, **kwargs: (args, kwargs)
    sys.modules['aiogram.types'] = types_mod

    types_login_url = types.ModuleType('aiogram.types.login_url')
    types_login_url.LoginUrl = lambda **kwargs: kwargs
    sys.modules['aiogram.types.login_url'] = types_login_url

    types_input_media_photo = types.ModuleType('aiogram.types.input_media_photo')
    types_input_media_photo.InputMediaPhoto = lambda **kwargs: kwargs
    sys.modules['aiogram.types.input_media_photo'] = types_input_media_photo

    enums = types.ModuleType('aiogram.enums')
    enums.ChatType = ChatTypeStub
    enums.ParseMode = types.SimpleNamespace(HTML='HTML')
    sys.modules['aiogram.enums'] = enums

    message_entity_type = types.ModuleType('aiogram.enums.message_entity_type')
    message_entity_type.MessageEntityType = types.SimpleNamespace(BOT_COMMAND='bot_command')
    sys.modules['aiogram.enums.message_entity_type'] = message_entity_type

    exceptions = types.ModuleType('aiogram.exceptions')
    exceptions.TelegramBadRequest = TelegramBadRequestStub
    exceptions.TelegramForbiddenError = TelegramForbiddenErrorStub
    exceptions.TelegramNetworkError = TelegramNetworkErrorStub
    sys.modules['aiogram.exceptions'] = exceptions

    fsm_context = types.ModuleType('aiogram.fsm.context')
    fsm_context.FSMContext = object
    sys.modules['aiogram.fsm.context'] = fsm_context

    fsm_state = types.ModuleType('aiogram.fsm.state')
    fsm_state.StatesGroup = StatesGroupStub
    fsm_state.State = StateStub
    sys.modules['aiogram.fsm.state'] = fsm_state

    storage_memory = types.ModuleType('aiogram.fsm.storage.memory')
    storage_memory.MemoryStorage = MemoryStorageStub
    sys.modules['aiogram.fsm.storage.memory'] = storage_memory

    storage_redis = types.ModuleType('aiogram.fsm.storage.redis')
    storage_redis.RedisStorage = RedisStorageStub
    storage_redis.DefaultKeyBuilder = DefaultKeyBuilderStub
    sys.modules['aiogram.fsm.storage.redis'] = storage_redis

    client_default = types.ModuleType('aiogram.client.default')
    client_default.DefaultBotProperties = lambda **kwargs: kwargs
    sys.modules['aiogram.client.default'] = client_default

    client_telegram = types.ModuleType('aiogram.client.telegram')
    client_telegram.TelegramAPIServer = types.SimpleNamespace(
        from_base=lambda *_args, **_kwargs: object(),
    )
    sys.modules['aiogram.client.telegram'] = client_telegram

    client_session = types.ModuleType('aiogram.client.session.aiohttp')
    client_session.AiohttpSession = lambda **kwargs: kwargs
    sys.modules['aiogram.client.session.aiohttp'] = client_session

    apscheduler_asyncio = types.ModuleType('apscheduler.schedulers.asyncio')
    apscheduler_asyncio.AsyncIOScheduler = lambda: types.SimpleNamespace(
        add_job=lambda *_args, **_kwargs: True,
        start=lambda: None,
    )
    apscheduler = types.ModuleType('apscheduler')
    apscheduler.__path__ = []
    sys.modules['apscheduler'] = apscheduler
    apscheduler_schedulers = types.ModuleType('apscheduler.schedulers')
    apscheduler_schedulers.__path__ = []
    sys.modules['apscheduler.schedulers'] = apscheduler_schedulers
    sys.modules['apscheduler.schedulers.asyncio'] = apscheduler_asyncio

    redis_mod = types.ModuleType('redis')
    redis_mod.__path__ = []
    redis_asyncio = types.ModuleType('redis.asyncio')
    redis_asyncio.Redis = RedisClientStub
    redis_mod.asyncio = redis_asyncio
    sys.modules['redis'] = redis_mod
    sys.modules['redis.asyncio'] = redis_asyncio

    aiohttp = types.ModuleType('aiohttp')
    aiohttp.ClientTimeout = lambda **kwargs: kwargs
    aiohttp.ContentTypeError = ValueError

    class FormDataStub:
        def __init__(self):
            self.fields = []

        def add_field(self, *args, **kwargs):
            self.fields.append((args, kwargs))

    aiohttp.FormData = FormDataStub
    sys.modules['aiohttp'] = aiohttp

    qrcode_mod = types.ModuleType('qrcode')
    qrcode_mod.make = lambda *_args, **_kwargs: types.SimpleNamespace(
        save=lambda *_save_args, **_save_kwargs: None,
    )
    sys.modules['qrcode'] = qrcode_mod

    pil_mod = types.ModuleType('PIL')
    pil_mod.__path__ = []
    image_mod = types.ModuleType('PIL.Image')
    image_mod.open = lambda *_args, **_kwargs: types.SimpleNamespace()
    sys.modules['PIL'] = pil_mod
    sys.modules['PIL.Image'] = image_mod

    if stub_common:
        common = types.ModuleType('common')

        class KeyboardTypeStub:
            RENTAL_CONTACT = 81
            RENTAL_BOOK = 82
            RENTAL_RESERVATION_ACTION = 83
            SEP = '~'

        class RcacheStub:
            KEY_SEP = '~'
            RENTAL_DESC_PREFIX = 'rental_desc'
            RENTAL_PAYMENT_PROOF_PREFIX = 'rental_payment_proof'

        class MiscStub:
            MSG_ERROR_API = 'api error'
            RE_KEY_SEP = r'^%s%s'

            @staticmethod
            def get_html_a(href, text):
                return '<a href="%s">%s</a>' % (href, text)

            @staticmethod
            def get_start_deeplink(start_payload, https=False):
                prefix = 'https://' if https else ''
                return f'{prefix}t.me/{me.bot_data.username}?start={start_payload}'

            @staticmethod
            def get_deeplink_with_name(profile):
                return profile.get('first_name') or profile.get('username') or str(profile.get('uuid', ''))

            @staticmethod
            def reply_markup_cancel_row():
                return InlineKeyboardMarkupStub(inline_keyboard=[])

            @staticmethod
            async def post_tg_user(_user):
                return 200, {'uuid': 'requester-uuid', 'first_name': 'Requester'}

            @staticmethod
            async def get_file_bytes(_voice):
                return b'voice'

            @staticmethod
            def redis_is_key_first_up(_key):
                return True

            @staticmethod
            async def redis_wait_last_in_pack(_key):
                return True

            @staticmethod
            async def check_none_n_clear(value, _state):
                return value is not None

        class TgDescStub:
            @staticmethod
            def from_message(_message, uuid_pack):
                return {'uuid_pack': uuid_pack, 'file_type': 'text'}

        common.Misc = MiscStub
        common.KeyboardType = KeyboardTypeStub
        common.Rcache = RcacheStub
        common.TgDesc = TgDescStub
        sys.modules['common'] = common
    else:
        sys.modules.pop('common', None)

    handler_bot = types.ModuleType('handler_bot')

    async def is_it_command(_message, _state):
        return False

    handler_bot.is_it_command = is_it_command
    handler_bot.MorphAnalyzer = object()
    sys.modules['handler_bot'] = handler_bot


class FakeState:
    def __init__(self, data=None):
        self.data = data or {}
        self.state = None
        self.cleared = False

    async def set_state(self, state):
        self.state = state

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def get_data(self):
        return dict(self.data)

    async def clear(self):
        self.cleared = True
        self.state = None
        self.data = {}


class FakeMessage:
    def __init__(self, text='', content_type=ContentTypeStub.TEXT):
        self.text = text
        self.caption = ''
        self.content_type = content_type
        self.from_user = types.SimpleNamespace(
            id=1001,
            username='requester',
            first_name='Requester',
            last_name='',
        )
        self.chat = types.SimpleNamespace(id=2002, type=ChatTypeStub.PRIVATE)
        self.message_id = 3003
        self.photo = None
        self.audio = None
        self.video = None
        self.document = None
        self.voice = None
        self.location = None
        self.media_group_id = ''
        self.replies = []

    async def reply(self, text, reply_markup=None, **kwargs):
        sent = FakeMessage()
        sent.text = text
        sent.reply_markup = reply_markup
        sent.kwargs = kwargs
        sent.chat = self.chat
        sent.message_id = 4004 + len(self.replies)
        self.replies.append(sent)
        return sent


class FakeCallback:
    def __init__(self, data):
        self.id = 'callback-id'
        self.data = data
        self.from_user = types.SimpleNamespace(id=1001, username='requester')
        self.message = FakeMessage()
        self.answered = False
        self.answer_text = None
        self.answer_show_alert = False

    async def answer(self, text=None, show_alert=False):
        self.answered = True
        self.answer_text = text
        self.answer_show_alert = show_alert


class FakeBot:
    def __init__(self, fail_send=False):
        self.fail_send = fail_send
        self.sent_messages = []
        self.sent_photos = []
        self.copied_messages = []
        self.edited_messages = []
        self.callback_answers = []

    async def send_message(self, chat_id, text, reply_markup=None, **kwargs):
        if self.fail_send:
            raise TelegramForbiddenErrorStub('blocked')
        self.sent_messages.append((chat_id, text, reply_markup, kwargs))

    async def send_photo(self, chat_id, photo, caption=None, reply_markup=None, **kwargs):
        if self.fail_send:
            raise TelegramForbiddenErrorStub('blocked')
        self.sent_photos.append((chat_id, photo, caption, reply_markup, kwargs))

    async def copy_message(self, chat_id, from_chat_id, message_id, **kwargs):
        if self.fail_send:
            raise TelegramForbiddenErrorStub('blocked')
        self.copied_messages.append((chat_id, from_chat_id, message_id, kwargs))

    async def edit_message_text(self, chat_id, message_id, text, reply_markup=None, **kwargs):
        self.edited_messages.append((chat_id, message_id, text, reply_markup, kwargs))

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        self.callback_answers.append((callback_query_id, text, show_alert))


def import_fresh(module_name):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


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


class LegacyRelativesCallbackFeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.common = import_fresh('common')
        self.handler_relatives = import_fresh('handler_relatives')

    async def test_malformed_parent_callback_shows_notice_and_skips_auth(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.FATHER}{self.common.KeyboardType.SEP}'
        )

        with mock.patch.object(
            self.handler_relatives.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(),
        ) as check_owner:
            await self.handler_relatives.cbq_papa_mama(callback, FakeState())

        check_owner.assert_not_awaited()
        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('кнопка устарела', callback.answer_text.lower())

    async def test_parent_callback_auth_failure_shows_profile_notice(self):
        callback = FakeCallback(
            f'{self.common.KeyboardType.FATHER}{self.common.KeyboardType.SEP}person-uuid'
        )

        with mock.patch.object(
            self.handler_relatives.Misc,
            'check_owner_by_uuid',
            mock.AsyncMock(return_value=False),
        ):
            await self.handler_relatives.cbq_papa_mama(callback, FakeState())

        self.assertTrue(callback.answered)
        self.assertTrue(callback.answer_show_alert)
        self.assertIn('профиль', callback.answer_text.lower())

    async def test_new_parent_command_interrupt_stops_profile_creation(self):
        message = FakeMessage(text='/map')
        state = FakeState({'uuid': 'person-uuid', 'is_father': True})

        with mock.patch.object(
            self.handler_relatives,
            'is_it_command',
            mock.AsyncMock(return_value=True),
        ), mock.patch.object(
            self.handler_relatives.Misc,
            'api_request',
            mock.AsyncMock(),
        ) as api_request:
            await self.handler_relatives.put_new_papa_mama(message, state)

        api_request.assert_not_awaited()
        self.assertEqual(message.replies, [])


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


class OfferRuntimeDeeplinkTests(unittest.TestCase):
    def setUp(self):
        install_dependency_stubs(stub_common=False)
        self.handler_offer = import_fresh('handler_offer')

    def test_offer_deeplink_uses_runtime_bot_username_and_preserves_ref_payload(self):
        self.assertEqual(
            self.handler_offer.Offer.get_deeplink('offer-uuid', 'sender-ref'),
            't.me/DoveraBot?start=offer-offer-uuid-userId-sender-ref',
        )


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


class MainStorageTests(unittest.TestCase):
    def setUp(self):
        install_dependency_stubs()
        self.main = import_fresh('main')

    def test_build_fsm_storage_uses_redis_by_default(self):
        storage = self.main.build_fsm_storage()

        self.assertIsInstance(storage, RedisStorageStub)
        self.assertEqual(storage.redis.kwargs['db'], 2)
        self.assertEqual(storage.key_builder.prefix, 'doverabot:fsm')

    def test_build_fsm_storage_can_use_memory_for_local_override(self):
        self.main.settings.BOT_FSM_STORAGE = 'memory'

        self.assertIsInstance(self.main.build_fsm_storage(), MemoryStorageStub)


if __name__ == '__main__':
    unittest.main()
