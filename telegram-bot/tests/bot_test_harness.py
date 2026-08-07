import html as std_html
import importlib
import sys
import types
from pathlib import Path


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
    PINNED_MESSAGE = 'pinned_message'


class ChatTypeStub:
    PRIVATE = 'private'
    GROUP = 'group'
    SUPERGROUP = 'supergroup'
    CHANNEL = 'channel'


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
    settings.RENTAL_STT_TIMEOUT = 300
    settings.RENTAL_LLM_EXTRACTOR_CONTRACT = 'doverabot_rental_llm_extractor_v1'
    settings.RENTAL_LLM_EXTRACTOR_URL = ''
    settings.RENTAL_LLM_EXTRACTOR_TOKEN = ''
    settings.RENTAL_LLM_EXTRACTOR_MODEL = ''
    settings.RENTAL_LLM_EXTRACTOR_TIMEOUT = 30
    settings.RENTAL_GEOCODING_CONTRACT = 'doverabot_rental_geocoding_v1'
    settings.RENTAL_GEOCODING_URL = ''
    settings.RENTAL_GEOCODING_TOKEN = ''
    settings.RENTAL_GEOCODING_LIMIT = 3
    settings.RENTAL_GEOCODING_SEARCH_DELTA = 0.05
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
    types_mod.MessageOriginUser = type('MessageOriginUser', (), {})
    types_mod.MessageOriginHiddenUser = type('MessageOriginHiddenUser', (), {})
    types_mod.MessageOriginChat = type('MessageOriginChat', (), {})
    types_mod.MessageOriginChannel = type('MessageOriginChannel', (), {})
    types_mod.LinkPreviewOptions = lambda **kwargs: kwargs
    sys.modules['aiogram.types'] = types_mod

    types_login_url = types.ModuleType('aiogram.types.login_url')
    types_login_url.LoginUrl = lambda **kwargs: kwargs
    sys.modules['aiogram.types.login_url'] = types_login_url

    types_web_app_info = types.ModuleType('aiogram.types.web_app_info')
    types_web_app_info.WebAppInfo = lambda **kwargs: kwargs
    sys.modules['aiogram.types.web_app_info'] = types_web_app_info

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

    pymorphy3_mod = types.ModuleType('pymorphy3')
    pymorphy3_mod.MorphAnalyzer = lambda: object()
    sys.modules['pymorphy3'] = pymorphy3_mod

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
            RENTAL_OWNER_ACTION = 84
            RENTAL_GEOCODE = 85
            RENTAL_OFFER_DRAFT = 86
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
            def check_location_str(_text):
                return None, None

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
            def from_message(message, uuid_pack):
                file_type = 'text'
                file_id = ''
                for candidate in ('photo', 'audio', 'video', 'document', 'voice'):
                    content = getattr(message, candidate, None)
                    if not content:
                        continue
                    file_type = candidate
                    if candidate == 'photo' and isinstance(content, list) and content:
                        file_id = getattr(content[-1], 'file_id', '')
                    else:
                        file_id = getattr(content, 'file_id', '')
                    break
                return {
                    'uuid_pack': uuid_pack,
                    'file_type': file_type,
                    'file_id': file_id,
                    'media_group_id': getattr(message, 'media_group_id', '') or '',
                    'message_id': getattr(message, 'message_id', 0),
                    'chat_id': getattr(getattr(message, 'chat', None), 'id', 0),
                    'caption': getattr(message, 'caption', '') or '',
                }

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
            is_bot=False,
        )
        self.chat = types.SimpleNamespace(id=2002, type=ChatTypeStub.PRIVATE)
        self.message_id = 3003
        self.forward_origin = None
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
